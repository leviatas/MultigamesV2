#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Flujo de Telegram de Carrera de Bichos: apuestas en serpiente, aportes secretos al
# mazo y la carrera transmitida en vivo editando un mensaje carta por carta.

import asyncio
import logging as log
import re

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

from Utils import get_game, save, player_call
from Utils.animacion import lanzar, en_curso, enviar, editar
from Constants.Config import ADMIN
from CarreraBichos.Boardgamebox.Game import Game
from CarreraBichos.Boardgamebox.State import Bicho
from CarreraBichos.Constants.Cartas import (
    ORDEN_BICHOS, CANTIDAD_CARRERAS, DINERO_INICIAL, MANO_INICIAL, PAUSA_CARTA, APUESTAS_ESPECIALES,
    MULTA_FUERTE, MULTIPLICADOR_FINAL, carta_txt, bicho_txt,
)
import CarreraBichos.Motor as M

import GamesController

logger = log.getLogger(__name__)

TIPO = "CarreraBichos"
GUARDAR_CADA = 6


def clave_tarea(cid):
    return "CB-{}".format(cid)


def teclado(cid, comando, uid, opciones, columnas=1):
    filas, fila = [], []
    for clave, texto in opciones.items():
        fila.append(InlineKeyboardButton(texto, callback_data="{}*{}*{}*{}".format(cid, comando, clave, uid)))
        if len(fila) == columnas:
            filas.append(fila)
            fila = []
    if fila:
        filas.append(fila)
    return InlineKeyboardMarkup(filas)


def destino_privado(game, uid):
    return ADMIN[0] if game.is_debugging else uid


def es_actor_valido(game, actor_uid, uid_esperado):
    return actor_uid == uid_esperado or (game.is_debugging and actor_uid == ADMIN[0])


def _parse(callback_data, comando):
    regex = re.search(r"(-[0-9]*)\*" + comando + r"\*(.*)\*([0-9]*)", callback_data)
    if not regex:
        return None, None, None
    return int(regex.group(1)), regex.group(2), int(regex.group(3))


def _juego(cid):
    game = get_game(cid)
    if not game or game.tipo != TIPO or not game.board:
        return None
    return game


def _sigue_vigente(game):
    """False si la partida se borró o se reemplazó mientras corría una tarea."""
    return GamesController.games.get(game.cid) is game


async def _responder(callback, texto=None):
    try:
        await callback.answer(texto)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Inicio
# ---------------------------------------------------------------------------

async def init_game(bot, game):
    try:
        game.shuffle_player_sequence()
        for p in game.player_sequence:
            p.dinero = DINERO_INICIAL
            p.mano = [M.carta_al_azar() for _ in range(MANO_INICIAL)]
            p.apuestas = []
        await bot.send_message(
            game.cid,
            "🏟️ *¡Bienvenidos a la Carrera de Bichos!*\n\n"
            "{}\n\n"
            "Cada uno arranca con *${}*. Se corren *{} carreras*: antes de cada una apuestan, "
            "meten en secreto una carta al mazo y después... ¡a gritar frente a la pantalla! 📺\n"
            "Usá /rules para el reglamento y /info para ver tu mano.".format(
                "\n".join(bicho_txt(b) for b in ORDEN_BICHOS), DINERO_INICIAL, CANTIDAD_CARRERAS),
            parse_mode=ParseMode.MARKDOWN
        )
        await iniciar_apuestas(bot, game)
    except Exception as e:
        logger.error("CB init_game error: %s", e)
        await bot.send_message(ADMIN[0], "CB init_game error: {}".format(e))
        raise


def _primer_apostador(game):
    st = game.board.state
    seq = game.player_sequence
    if st.carrera == 1 or st.primer_apostador_uid is None:
        return seq[0]
    # El que tiene menos plata elige primero (desempata el que sigue al anterior).
    previo = game.playerlist.get(st.primer_apostador_uid)
    i0 = (seq.index(previo) + 1) % len(seq) if previo in seq else 0
    rotada = seq[i0:] + seq[:i0]
    minimo = min(p.dinero for p in seq)
    return [p for p in rotada if p.dinero == minimo][0]


async def iniciar_apuestas(bot, game):
    st = game.board.state
    st.fase_actual = "Apuestas"
    st.bichos = [Bicho(b) for b in ORDEN_BICHOS]
    st.podio = []
    st.aportes = {}
    st.mazo_base = M.armar_mazo_base()
    M.preparar_apuestas(st)
    for p in game.player_sequence:
        p.apuestas = []
        p.aporto = False

    primero = _primer_apostador(game)
    st.primer_apostador_uid = primero.uid
    seq = game.player_sequence
    i0 = seq.index(primero)
    ida = seq[i0:] + seq[:i0]
    st.orden_apuestas = []
    for r in range(game.apuestas_por_jugador()):
        st.orden_apuestas += [p.uid for p in (ida if r % 2 == 0 else list(reversed(ida)))]
    st.apuesta_idx = 0
    st.boleto_pendiente = None

    pregunta = APUESTAS_ESPECIALES[st.especial][0]
    final = st.carrera == CANTIDAD_CARRERAS
    texto = "🎟️ *Carrera {}/{} — ¡Hagan sus apuestas!*{}\n\n".format(
        st.carrera, CANTIDAD_CARRERAS, "\n🔥🔥 *CARRERA FINAL: todo paga x{}* 🔥🔥".format(MULTIPLICADOR_FINAL) if final else "")
    texto += "🃏 *Mazo base (público)* — {} cartas:\n{}\n".format(
        len(st.mazo_base), ", ".join(carta_txt(c) for c in M.ordenar_para_mostrar(st.mazo_base)))
    texto += "_(+ una carta secreta de cada jugador)_\n\n"
    texto += "❓ *Apuesta especial:* {}\n\n".format(pregunta)
    texto += "Cada uno toma {} boletos. Normal: si pierde, $0. 🔥 Fuerte: cobra doble, si pierde paga ${}.".format(
        game.apuestas_por_jugador(), MULTA_FUERTE)
    await enviar(bot, game.cid, texto)
    await pedir_apuesta(bot, game)


def _tablon(game):
    st = game.board.state
    lineas = []
    for b in ORDEN_BICHOS:
        g, pd = st.boletos.get("G_" + b, []), st.boletos.get("P_" + b, [])
        lineas.append("{}  🏆 {}   🥈 {}".format(
            bicho_txt(b),
            "${}".format(g[0]) if g else "agotado",
            "${}".format(pd[0]) if pd else "agotado"))
    si, no = st.boletos.get("SI", []), st.boletos.get("NO", [])
    lineas.append("❓ SÍ {}   NO {}".format("${}".format(si[0]) if si else "agotado",
                                         "${}".format(no[0]) if no else "agotado"))
    return "\n".join(lineas)


async def pedir_apuesta(bot, game):
    st = game.board.state
    uid = st.orden_apuestas[st.apuesta_idx]
    jugador = game.playerlist[uid]
    opciones = {}
    for b in ORDEN_BICHOS:
        for pref in ("G_", "P_"):
            pila = st.boletos.get(pref + b, [])
            if pila:
                opciones[pref + b] = M.boleto_boton(pref + b, pila[0])
    for clave in ("SI", "NO"):
        if st.boletos.get(clave):
            opciones[clave] = M.boleto_boton(clave, st.boletos[clave][0])
    texto = "🎟️ *Boletos disponibles*\n{}\n\n👉 {} elige su boleto ({}/{}) — tenés ${}".format(
        _tablon(game), player_call(jugador),
        sum(1 for u in st.orden_apuestas[:st.apuesta_idx + 1] if u == uid), game.apuestas_por_jugador(),
        jugador.dinero)
    msg = await enviar(bot, game.cid, texto, reply_markup=teclado(game.cid, "betCB", uid, opciones, columnas=2))
    st.apuesta_msg_id = msg.message_id if msg else None
    await save(bot, game.cid)


async def preguntar_modo(bot, game, message_id):
    st = game.board.state
    uid = st.orden_apuestas[st.apuesta_idx]
    jugador = game.playerlist[uid]
    clave = st.boleto_pendiente
    pago = st.boletos[clave][0]
    mult = MULTIPLICADOR_FINAL if st.carrera == CANTIDAD_CARRERAS else 1
    texto = "{} eligió *{}*.\n¿Cómo la jugás?".format(jugador.name, M.boleto_txt(game, clave))
    opciones = {
        "N": "🙂 Normal: gana ${}".format(pago * mult),
        "F": "🔥 Fuerte: gana ${} / pierde ${}".format(pago * 2 * mult, MULTA_FUERTE * mult),
        "X": "↩️ Elegir otro",
    }
    markup = teclado(game.cid, "modCB", uid, opciones)
    if message_id is None or not await editar(bot, game.cid, message_id, texto, reply_markup=markup):
        await enviar(bot, game.cid, texto, reply_markup=markup)


async def callback_boleto(update: Update, context: CallbackContext):
    bot = context.bot
    callback = update.callback_query
    try:
        cid, clave, uid = _parse(callback.data, "betCB")
        game = _juego(cid)
        if not game:
            return await _responder(callback)
        st = game.board.state
        if (st.fase_actual != "Apuestas" or st.boleto_pendiente is not None
                or st.orden_apuestas[st.apuesta_idx] != uid or not st.boletos.get(clave)):
            return await _responder(callback, "Ese boleto ya no está disponible.")
        if not es_actor_valido(game, callback.from_user.id, uid):
            return await _responder(callback, "No es tu turno de apostar.")
        await _responder(callback)
        st.boleto_pendiente = clave
        await save(bot, cid)
        await preguntar_modo(bot, game, callback.message.message_id)
    except Exception as e:
        await bot.send_message(ADMIN[0], "CB callback_boleto error: {}".format(e))


async def callback_modo(update: Update, context: CallbackContext):
    bot = context.bot
    callback = update.callback_query
    try:
        cid, modo, uid = _parse(callback.data, "modCB")
        game = _juego(cid)
        if not game:
            return await _responder(callback)
        st = game.board.state
        clave = st.boleto_pendiente
        if (st.fase_actual != "Apuestas" or clave is None or st.orden_apuestas[st.apuesta_idx] != uid
                or modo not in ("N", "F", "X")):
            return await _responder(callback, "Ese botón ya no vale.")
        if not es_actor_valido(game, callback.from_user.id, uid):
            return await _responder(callback, "No es tu turno de apostar.")
        await _responder(callback)

        jugador = game.playerlist[uid]
        st.boleto_pendiente = None
        if modo == "X" or not st.boletos.get(clave):
            await editar(bot, cid, callback.message.message_id, "↩️ {} vuelve a elegir.".format(jugador.name), parse_mode=None)
            await pedir_apuesta(bot, game)
            return

        pago = st.boletos[clave].pop(0)
        fuerte = modo == "F"
        jugador.apuestas.append({"t": clave, "pago": pago, "fuerte": fuerte})
        await editar(bot, cid, callback.message.message_id, "✅ {} apuesta {}{} (paga ${})".format(
            jugador.name, M.boleto_txt(game, clave), " 🔥 FUERTE" if fuerte else "", pago))
        st.apuesta_idx += 1
        if st.apuesta_idx < len(st.orden_apuestas):
            await pedir_apuesta(bot, game)
            return
        await iniciar_aportes(bot, game)
    except Exception as e:
        await bot.send_message(ADMIN[0], "CB callback_modo error: {}".format(e))


# ---------------------------------------------------------------------------
# Aportes secretos al mazo
# ---------------------------------------------------------------------------

async def iniciar_aportes(bot, game):
    st = game.board.state
    st.fase_actual = "Aportes"
    resumen = "\n".join("• *{}*: {}".format(
        p.name, ", ".join(M.boleto_boton(a["t"], a["pago"]) + ("🔥" if a["fuerte"] else "") for a in p.apuestas))
        for p in game.player_sequence)
    await enviar(bot, game.cid,
                 "📋 *Apuestas cerradas*\n{}\n\n🤫 Ahora cada uno mete *en secreto* una carta de su mano al "
                 "mazo. ¡Revisen el privado!".format(resumen))
    await save(bot, game.cid)
    for p in game.player_sequence:
        await pedir_aporte(bot, game, p)


async def pedir_aporte(bot, game, jugador):
    st = game.board.state
    opciones = {str(i): carta_txt(c) for i, c in enumerate(jugador.mano)}
    apuestas = ", ".join(M.boleto_boton(a["t"], a["pago"]) + ("🔥" if a["fuerte"] else "") for a in jugador.apuestas)
    texto = "🏟️ *{}* — carrera {}\nTus apuestas: {}\n\n🤫 ¿Qué carta metés en el mazo?".format(
        game.groupName, st.carrera, apuestas or "-")
    try:
        await bot.send_message(destino_privado(game, jugador.uid), texto, parse_mode=ParseMode.MARKDOWN,
                               reply_markup=teclado(game.cid, "aporCB", jugador.uid, opciones))
    except Exception as e:
        logger.warning("CB pedir_aporte: %s", e)
        await enviar(bot, game.cid,
                     "{} no puedo escribirte por privado. Abrí el chat con el bot, tocá Start y usá /call.".format(
                         player_call(jugador)))


async def callback_aporte(update: Update, context: CallbackContext):
    bot = context.bot
    callback = update.callback_query
    try:
        cid, idx, uid = _parse(callback.data, "aporCB")
        game = _juego(cid)
        if not game or game.board.state.fase_actual != "Aportes":
            return await _responder(callback, "Ya no se pueden aportar cartas.")
        if not es_actor_valido(game, callback.from_user.id, uid):
            return await _responder(callback)
        st = game.board.state
        jugador = game.playerlist.get(uid)
        if not jugador or jugador.aporto or not idx.isdigit() or int(idx) >= len(jugador.mano):
            return await _responder(callback, "Ya aportaste tu carta.")
        await _responder(callback)

        carta = jugador.mano.pop(int(idx))
        st.aportes[str(uid)] = carta
        jugador.aporto = True
        await editar(bot, callback.message.chat_id, callback.message.message_id,
                     "🤫 Metiste *{}* en el mazo. ¡Que gane el mejor!".format(carta_txt(carta)))

        faltan = [p for p in game.player_sequence if not p.aporto]
        if faltan:
            await enviar(bot, cid, "🃏 {} ya metió su carta. Faltan: {}".format(
                jugador.name, ", ".join(p.name for p in faltan)), parse_mode=None)
            await save(bot, cid)
            return
        await largar(bot, game)
    except Exception as e:
        await bot.send_message(ADMIN[0], "CB callback_aporte error: {}".format(e))


# ---------------------------------------------------------------------------
# La carrera, en vivo
# ---------------------------------------------------------------------------

async def largar(bot, game):
    st = game.board.state
    M.preparar_carrera(st, list(st.aportes.values()))
    st.fase_actual = "Carrera"
    await save(bot, game.cid)
    lanzar(clave_tarea(game.cid), transmitir(bot, game))


async def transmitir(bot, game, retomar=False):
    st = game.board.state
    cid = game.cid
    try:
        titulo = "Carrera {}/{}".format(st.carrera, CANTIDAD_CARRERAS)
        if retomar:
            msg = await enviar(bot, cid, M.cuadro_en_vivo(st, titulo="🔴 *SE RETOMA LA TRANSMISIÓN* — " + titulo))
        else:
            msg = await enviar(bot, cid, M.cuadro_en_vivo(
                st, titulo="*{}* — los bichos se acomodan en la largada...".format(titulo)))
        if msg is None:
            raise RuntimeError("no se pudo enviar el mensaje de la carrera")
        st.live_msg_id = msg.message_id

        if not retomar:
            for paso in ("3️⃣ ...", "2️⃣ ...", "1️⃣ ... 🔥 se queman {} cartas boca abajo".format(len(st.quemadas)),
                         "🔫 *¡¡LARGARON!!*"):
                await asyncio.sleep(1.5)
                await editar(bot, cid, st.live_msg_id,
                             M.cuadro_en_vivo(st, eventos=[], titulo="*{}* — {}".format(titulo, paso)))
            await asyncio.sleep(1.0)

        desde_guardado = 0
        while not M.carrera_terminada(st):
            if not _sigue_vigente(game):
                return
            cartas, eventos = [], []
            for _ in range(M.cartas_por_cuadro(st)):
                if M.carrera_terminada(st):
                    break
                carta, ev = M.paso_de_carrera(st)
                cartas.append(carta)
                eventos += ev
            await editar(bot, cid, st.live_msg_id, M.cuadro_en_vivo(st, cartas, eventos))
            desde_guardado += 1
            if desde_guardado >= GUARDAR_CADA:
                desde_guardado = 0
                await save(bot, cid)
            pausa = PAUSA_CARTA
            if any("🏁" in e for e in eventos):
                pausa += 1.8  # que se saboree el cruce de meta
            elif any("😱" in e for e in eventos):
                pausa += 0.6
            await asyncio.sleep(pausa)

        if not _sigue_vigente(game):
            return
        await editar(bot, cid, st.live_msg_id, M.cuadro_en_vivo(
            st, eventos=st.ticker + ["🏁 *¡TERMINÓ LA CARRERA!*"], titulo="🏁 *FINAL* — {}".format(titulo)))
        await terminar_carrera(bot, game)
    except Exception as e:
        logger.exception("CB transmitir error")
        await bot.send_message(ADMIN[0], "CB transmitir error en {}: {}".format(cid, e))
        await enviar(bot, cid, "⚠️ Se cortó la transmisión. Usen /call para retomarla.", parse_mode=None)


async def terminar_carrera(bot, game):
    st = game.board.state
    if st.fase_actual != "Carrera":
        return
    st.fase_actual = "Pagos"

    podio = "\n".join("{} {}".format(M.MEDALLAS[i + 1], bicho_txt(b)) for i, b in enumerate(st.podio))
    pregunta = APUESTAS_ESPECIALES[st.especial][0]
    especial = "❓ {} → *{}*".format(pregunta, "SÍ" if M.especial_cumplida(st) else "NO")
    secretos = "\n".join("• {} metió {}".format(game.playerlist[int(u)].name, carta_txt(c))
                         for u, c in st.aportes.items() if int(u) in game.playerlist)
    pagos = M.pagar_apuestas(game)
    texto = ("🏆 *Resultado de la carrera {}* ({} cartas)\n{}\n\n{}\n\n🤫 *Las cartas secretas:*\n{}\n\n"
             "💰 *Pagos{}:*\n{}").format(
        st.carrera, st.reveladas, podio, especial, secretos,
        " (x{})".format(MULTIPLICADOR_FINAL) if st.carrera == CANTIDAD_CARRERAS else "", pagos)
    await enviar(bot, game.cid, texto)

    if st.carrera >= CANTIDAD_CARRERAS:
        await finalizar_juego(bot, game)
        return

    st.carrera += 1
    for p in game.player_sequence:
        while len(p.mano) < MANO_INICIAL:
            p.mano.append(M.carta_al_azar())
    await asyncio.sleep(2)
    await iniciar_apuestas(bot, game)


async def finalizar_juego(bot, game):
    st = game.board.state
    st.fase_actual = "Finalizado"
    maximo = max(p.dinero for p in game.player_sequence)
    ganadores = [p for p in game.player_sequence if p.dinero == maximo]
    st.ganadores_uids = [p.uid for p in ganadores]
    await save(bot, game.cid)
    tabla = "\n".join("{}. {} — ${}".format(i + 1, p.name, p.dinero)
                      for i, p in enumerate(sorted(game.player_sequence, key=lambda p: -p.dinero)))
    await enviar(bot, game.cid, "💰🏆 *¡{} {} la Carrera de Bichos con ${}!*\n\n{}".format(
        " y ".join(p.name for p in ganadores), "ganan" if len(ganadores) > 1 else "gana", maximo, tabla))
    await bot.send_message(
        game.cid, "¿Quieren seguir jugando?",
        reply_markup=teclado(game.cid, "chooseendCB", 1, {
            "Nuevo": "Nueva partida con nuevos jugadores",
            "Mismos": "Misma partida, mismos jugadores",
        })
    )


async def callback_finish_game_buttons_cb(update: Update, context: CallbackContext):
    bot = context.bot
    callback = update.callback_query
    try:
        cid, opcion, uid = _parse(callback.data, "chooseendCB")
        game = get_game(cid)
        if not game or game.tipo != TIPO or not game.board or game.board.state.fase_actual != "Finalizado":
            return await _responder(callback)
        await _responder(callback)
        await editar(bot, cid, callback.message.message_id, "Has elegido: {}".format(opcion), parse_mode=None)

        groupName, tipo, modo = game.groupName, game.tipo, game.modo
        players = game.playerlist.copy()
        new_game = Game(cid, callback.from_user.id, groupName, tipo, modo)
        GamesController.games[cid] = new_game

        if opcion == "Nuevo":
            await bot.send_message(
                cid, "Cada jugador puede unirse con /join. El iniciador puede escribir /startgame cuando todos estén listos.")
            await save(bot, cid)
            return

        for uid_p, p in players.items():
            new_game.add_player(uid_p, p.name)
        new_game.create_board()
        await init_game(bot, new_game)
    except Exception as e:
        await bot.send_message(ADMIN[0], "CB callback_finish_game_buttons_cb error: {}".format(e))


# ---------------------------------------------------------------------------
# Recordatorio (/call)
# ---------------------------------------------------------------------------

async def recordar(bot, game):
    st = game.board.state
    fase = st.fase_actual
    if fase == "Apuestas":
        if st.boleto_pendiente is not None:
            await preguntar_modo(bot, game, None)
        else:
            await pedir_apuesta(bot, game)
    elif fase == "Aportes":
        faltan = [p for p in game.player_sequence if not p.aporto]
        await enviar(bot, game.cid, "⏳ Falta que metan su carta secreta: {}".format(
            ", ".join(player_call(p) for p in faltan)))
        for p in faltan:
            await pedir_aporte(bot, game, p)
    elif fase == "Carrera":
        if en_curso(clave_tarea(game.cid)):
            await enviar(bot, game.cid, "📺 ¡La carrera está en vivo! Miren el mensaje de la transmisión.", parse_mode=None)
        else:
            lanzar(clave_tarea(game.cid), transmitir(bot, game, retomar=True))
    elif fase == "Pagos":
        # Se cortó entre el final de la carrera y las apuestas siguientes.
        st.fase_actual = "Carrera"
        await terminar_carrera(bot, game)
