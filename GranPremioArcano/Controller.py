#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Flujo de Telegram de Gran Premio Arcano: configuración, draft, elección secreta de
# corredores y turnos con el dado animado de Telegram.

import asyncio
import logging as log
import random
import re

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

from Utils import get_game, save, player_call
from Utils.animacion import lanzar, en_curso, enviar, editar, tirar_dado, enviar_foto
from Constants.Config import ADMIN
from GranPremioArcano.Boardgamebox.Game import Game
from GranPremioArcano.Constants.Corredores import (
    CORREDORES, CANTIDAD_CARRERAS, NOMBRE_PISTA, DESCRIPCION_CASILLA, etiqueta, ficha,
)
import GranPremioArcano.Motor as M
import GranPremioArcano.render as R

import GamesController

logger = log.getLogger(__name__)

TIPO = "GranPremioArcano"
MAX_LINEAS_LOG = 35
# Telegram permite captions de hasta 1024 caracteres.
MAX_CAPTION = 1000


async def imagen_pista(game):
    """Bytes del PNG de la pista, o None si no se pudo renderizar (sin Chrome, etc.).
    El render lanza Chrome (~1 s): corre en un hilo para no trabar el bot."""
    try:
        buf = await asyncio.to_thread(R.render_pista, game)
        return buf.getvalue()
    except Exception as e:
        logger.warning("GP render de la pista falló, uso texto: %s", e)
        return None


async def enviar_pista(bot, game, encabezado, pie, reply_markup=None):
    """Manda la pista como imagen con `encabezado` + `pie` de caption (y los botones).

    Si el texto no entra en el caption, el encabezado va antes como mensaje aparte.
    Si la imagen falla, manda todo como texto con la pista dibujada en caracteres."""
    foto = await imagen_pista(game)
    if foto is not None:
        caption = (encabezado + "\n\n" if encabezado else "") + pie
        if len(caption) > MAX_CAPTION:
            if encabezado:
                await enviar(bot, game.cid, encabezado)
            caption = pie[:MAX_CAPTION]
        if await enviar_foto(bot, game.cid, foto, caption=caption, reply_markup=reply_markup):
            return
    texto = (encabezado + "\n\n" if encabezado else "") + M.dibujar_pista(game) + "\n" + pie
    await enviar(bot, game.cid, texto, reply_markup=reply_markup)


def clave_tarea(cid):
    return "GP-{}".format(cid)


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


async def _responder(callback, texto=None):
    try:
        await callback.answer(texto)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Inicio y configuración
# ---------------------------------------------------------------------------

async def init_game(bot, game):
    try:
        game.shuffle_player_sequence()
        st = game.board.state
        st.fase_actual = "Configurando"
        k = game.corredores_por_carrera()
        await bot.send_message(
            game.cid,
            "🏆 *¡Bienvenidos al Gran Premio Arcano!*\n\n"
            "Cada uno arma un equipo de *{} corredores* con poderes que rompen las reglas y "
            "los hace correr en *{} carreras*{}. Gana quien junte más puntos.\n"
            "Usá /rules para ver el reglamento completo.".format(
                4 * k, CANTIDAD_CARRERAS,
                " (con 2 jugadores, 2 corredores por carrera cada uno)" if k == 2 else ""
            ),
            parse_mode=ParseMode.MARKDOWN
        )
        await preguntar_reparto(bot, game)
        await save(bot, game.cid)
    except Exception as e:
        logger.error("GP init_game error: %s", e)
        await bot.send_message(ADMIN[0], "GP init_game error: {}".format(e))
        raise


async def preguntar_reparto(bot, game):
    opciones = {"draft": "🃏 Draft (elegir por turnos)", "azar": "🎲 Equipos al azar"}
    await bot.send_message(
        game.cid,
        "¿Cómo arman los equipos? (elige quien creó la partida)",
        reply_markup=teclado(game.cid, "repGP", game.initiator, opciones)
    )


async def callback_reparto(update: Update, context: CallbackContext):
    bot = context.bot
    callback = update.callback_query
    try:
        cid, opcion, uid = _parse(callback.data, "repGP")
        game = _juego(cid)
        if not game or game.board.state.fase_actual != "Configurando":
            return await _responder(callback)
        actor = callback.from_user.id
        if not (es_actor_valido(game, actor, uid) or actor in ADMIN):
            return await _responder(callback, "Elige quien creó la partida.")
        await _responder(callback)
        await editar(bot, cid, callback.message.message_id,
                     "Equipos: *{}*".format("draft" if opcion == "draft" else "al azar"))
        st = game.board.state
        st.reparto = opcion
        k = game.corredores_por_carrera()
        if opcion == "azar":
            M.repartir_al_azar(game, 4 * k)
            await anunciar_equipos(bot, game)
            await iniciar_eleccion(bot, game)
        else:
            st.mazo = list(CORREDORES.keys())
            random.shuffle(st.mazo)
            st.draft_ronda = 0
            st.draft_total_rondas = 2 * k
            await iniciar_ronda_draft(bot, game)
        await save(bot, cid)
    except Exception as e:
        await bot.send_message(ADMIN[0], "GP callback_reparto error: {}".format(e))


# ---------------------------------------------------------------------------
# Draft
# ---------------------------------------------------------------------------

async def iniciar_ronda_draft(bot, game):
    st = game.board.state
    st.fase_actual = "Draft"
    n = len(game.player_sequence)
    st.draft_cartas = [st.mazo.pop() for _ in range(2 * n)]
    inicio = st.draft_ronda % n
    seq = game.player_sequence[inicio:] + game.player_sequence[:inicio]
    st.draft_orden = [p.uid for p in seq] + [p.uid for p in reversed(seq)]
    st.draft_idx = 0
    await pedir_pick(bot, game)


def texto_draft(game):
    st = game.board.state
    lineas = ["🃏 *Draft — ronda {}/{}*\n".format(st.draft_ronda + 1, st.draft_total_rondas)]
    lineas += [ficha(r) for r in st.draft_cartas]
    return "\n".join(lineas)


async def pedir_pick(bot, game):
    st = game.board.state
    uid = st.draft_orden[st.draft_idx]
    jugador = game.playerlist[uid]
    opciones = {r: etiqueta(r) for r in st.draft_cartas}
    msg = await enviar(
        bot, game.cid,
        texto_draft(game) + "\n\n👉 Elige {}".format(player_call(jugador)),
        reply_markup=teclado(game.cid, "draftGP", uid, opciones, columnas=2)
    )
    st.draft_msg_id = msg.message_id if msg else None
    await save(bot, game.cid)


async def callback_draft(update: Update, context: CallbackContext):
    bot = context.bot
    callback = update.callback_query
    try:
        cid, rid, uid = _parse(callback.data, "draftGP")
        game = _juego(cid)
        if not game:
            return await _responder(callback)
        st = game.board.state
        if st.fase_actual != "Draft" or rid not in st.draft_cartas or st.draft_orden[st.draft_idx] != uid:
            return await _responder(callback, "Esa elección ya no está disponible.")
        if not es_actor_valido(game, callback.from_user.id, uid):
            return await _responder(callback, "No es tu turno de elegir.")
        await _responder(callback)

        jugador = game.playerlist[uid]
        st.draft_cartas.remove(rid)
        jugador.corredores.append(rid)
        await editar(bot, cid, callback.message.message_id,
                     "✅ {} eligió {}".format(jugador.name, ficha(rid)))
        st.draft_idx += 1

        if st.draft_idx < len(st.draft_orden):
            await pedir_pick(bot, game)
            return

        st.draft_ronda += 1
        if st.draft_ronda < st.draft_total_rondas:
            await iniciar_ronda_draft(bot, game)
            return

        await anunciar_equipos(bot, game)
        await iniciar_eleccion(bot, game)
        await save(bot, cid)
    except Exception as e:
        await bot.send_message(ADMIN[0], "GP callback_draft error: {}".format(e))


async def anunciar_equipos(bot, game):
    lineas = ["👥 *Equipos del Gran Premio*\n"]
    for p in game.player_sequence:
        lineas.append("*{}*: {}".format(p.name, ", ".join(etiqueta(r) for r in p.corredores)))
    lineas.append("\nCada uno puede ver los poderes de su equipo con /info.")
    await enviar(bot, game.cid, "\n".join(lineas))


# ---------------------------------------------------------------------------
# Elección secreta de corredores
# ---------------------------------------------------------------------------

async def iniciar_eleccion(bot, game):
    st = game.board.state
    st.fase_actual = "Eleccion"
    st.corredores = []
    k = game.corredores_por_carrera()
    pendientes = []
    for p in game.player_sequence:
        p.elegidos = []
        if len(p.disponibles()) <= k:
            p.elegidos = p.disponibles()
        else:
            pendientes.append(p)

    pista = M.tipo_pista(st)
    texto = "🏟️ *Carrera {}/{}* — {}\n".format(st.carrera, CANTIDAD_CARRERAS, NOMBRE_PISTA[pista])
    if pista == "salvaje":
        texto += "Casillas especiales: " + ", ".join(DESCRIPCION_CASILLA.values()) + "\n"
    if pendientes:
        texto += "\n🤫 Cada uno elija *en privado* qué corredor manda a esta carrera. Faltan: " + \
                 ", ".join(player_call(p) for p in pendientes)
    await enviar(bot, game.cid, texto)
    await save(bot, game.cid)

    for p in pendientes:
        await pedir_eleccion(bot, game, p)
    if not pendientes:
        await revelar_y_largar(bot, game)


async def pedir_eleccion(bot, game, jugador):
    st = game.board.state
    k = game.corredores_por_carrera()
    disponibles = jugador.disponibles()
    texto = "🏟️ *{}* — carrera {} ({})\n".format(game.groupName, st.carrera, NOMBRE_PISTA[M.tipo_pista(st)])
    if k == 2:
        texto += "Elegí el corredor {} de 2.\n".format(len(jugador.elegidos) + 1)
    texto += "\n" + "\n".join(ficha(r) for r in disponibles)
    try:
        await bot.send_message(
            destino_privado(game, jugador.uid), texto, parse_mode=ParseMode.MARKDOWN,
            reply_markup=teclado(game.cid, "elegGP", jugador.uid, {r: etiqueta(r) for r in disponibles})
        )
    except Exception as e:
        await bot.send_message(
            game.cid,
            "{} no puedo escribirte por privado. Abrí el chat con el bot, tocá Start y usá /call.".format(
                player_call(jugador)),
            parse_mode=ParseMode.MARKDOWN
        )
        logger.warning("GP pedir_eleccion: %s", e)


async def callback_eleccion(update: Update, context: CallbackContext):
    bot = context.bot
    callback = update.callback_query
    try:
        cid, rid, uid = _parse(callback.data, "elegGP")
        game = _juego(cid)
        if not game or game.board.state.fase_actual != "Eleccion":
            return await _responder(callback, "Esa elección ya no está disponible.")
        if not es_actor_valido(game, callback.from_user.id, uid):
            return await _responder(callback)
        jugador = game.playerlist.get(uid)
        k = game.corredores_por_carrera()
        if not jugador or rid not in jugador.disponibles() or len(jugador.elegidos) >= k:
            return await _responder(callback, "Esa elección ya no está disponible.")
        await _responder(callback)

        jugador.elegidos.append(rid)
        await editar(bot, callback.message.chat_id, callback.message.message_id,
                     "✅ Elegiste a {}".format(ficha(rid)))
        if len(jugador.elegidos) < k:
            await pedir_eleccion(bot, game, jugador)
            await save(bot, cid)
            return

        faltan = [p for p in game.player_sequence if len(p.elegidos) < k]
        if faltan:
            await enviar(bot, cid, "✅ {} ya eligió. Faltan: {}".format(
                jugador.name, ", ".join(p.name for p in faltan)))
            await save(bot, cid)
            return
        st = game.board.state
        st.fase_actual = "Largando"
        await save(bot, cid)
        lanzar(clave_tarea(cid), _tarea_segura(bot, game, revelar_y_largar(bot, game)))
    except Exception as e:
        await bot.send_message(ADMIN[0], "GP callback_eleccion error: {}".format(e))


async def revelar_y_largar(bot, game):
    st = game.board.state
    M.preparar_carrera(game)
    st.fase_actual = "Carrera"
    lineas = ["🎺 *¡Se presentan los corredores de la carrera {}!*\n".format(st.carrera)]
    for c in st.corredores:
        jugador = game.playerlist[c.uid]
        lineas.append("{} — de *{}*\n      _{}_".format(
            etiqueta(c.rid), jugador.name, CORREDORES[c.rid]["poder"]))
    primero = game.playerlist[st.corredores[st.orden_turnos[0]].uid]
    lineas.append("\nLarga {}.".format(player_call(primero)))
    await enviar(bot, game.cid, "\n".join(lineas))
    await save(bot, game.cid)
    await continuar_previas(bot, game)


async def continuar_previas(bot, game):
    """Elecciones antes de largar (Cambiante, Heredero, Suplente, Estratega, Alma Gemela)."""
    if M.siguiente_previa(game):
        await pedir_objetivo(bot, game)
        return
    await proximo_turno(bot, game)


# ---------------------------------------------------------------------------
# Turnos
# ---------------------------------------------------------------------------

def _relato(st):
    lineas = st.log[-MAX_LINEAS_LOG:]
    st.log = []
    return "\n".join(lineas)


async def proximo_turno(bot, game):
    st = game.board.state
    for _ in range(len(st.orden_turnos) * 3 + 1):
        if M.carrera_terminada(st):
            await terminar_carrera(bot, game)
            return
        if M.iniciar_turno(game):
            break
        M.avanzar_turno(game)
    await enviar_prompt_turno(bot, game)


async def enviar_prompt_turno(bot, game, relato=None):
    st = game.board.state
    c = M.corredor_actual(st)
    jugador = game.playerlist[c.uid]
    st.subfase = "Accion"
    relato = _relato(st) if relato is None else relato
    pie = "👉 Turno de {} — {}\n_{}_".format(
        M.nombre_corto(c), player_call(jugador), M.texto_poderes(c))
    opciones = {"{}_{}".format(st.turno_n, k): v for k, v in M.opciones_turno(game).items()}
    await enviar_pista(bot, game, relato, pie,
                       reply_markup=teclado(game.cid, "accGP", c.uid, opciones, columnas=2))
    await save(bot, game.cid)


def _validar_turno(game, data_key, uid, actor, subfase):
    st = game.board.state
    if st.fase_actual != "Carrera" or st.subfase != subfase:
        return None
    try:
        turno_n, accion = data_key.split("_", 1)
        turno_n = int(turno_n)
    except ValueError:
        return None
    c = M.corredor_actual(st)
    if c is None:
        return None
    # En las elecciones puede actuar otro jugador (el que adivina al Tramposo, o el
    # dueño de un corredor que elige antes de largar).
    esperado = st.pendiente.get("actor", c.uid) if subfase == "Objetivo" else c.uid
    if turno_n != st.turno_n or esperado != uid or not es_actor_valido(game, actor, uid):
        return None
    return accion


async def _quitar_botones(bot, callback):
    try:
        await bot.edit_message_reply_markup(callback.message.chat_id, callback.message.message_id, reply_markup=None)
    except Exception:
        pass


async def callback_accion(update: Update, context: CallbackContext):
    bot = context.bot
    callback = update.callback_query
    try:
        cid, data_key, uid = _parse(callback.data, "accGP")
        game = _juego(cid)
        if not game:
            return await _responder(callback)
        accion = _validar_turno(game, data_key, uid, callback.from_user.id, "Accion")
        if accion is None or accion not in M.opciones_turno(game):
            return await _responder(callback, "No es tu turno o ese botón ya no vale.")
        await _responder(callback)
        st = game.board.state
        await _quitar_botones(bot, callback)

        st.subfase = "Procesando"
        if M.tipo_accion(accion) == "objetivo":
            M.preparar_objetivo(game, accion)
            await save(bot, cid)
            lanzar(clave_tarea(cid), _tarea_segura(bot, game, pedir_objetivo(bot, game)))
            return
        await save(bot, cid)
        lanzar(clave_tarea(cid), _tarea_segura(bot, game, procesar_accion(bot, game, accion)))
    except Exception as e:
        await bot.send_message(ADMIN[0], "GP callback_accion error: {}".format(e))


async def pedir_objetivo(bot, game):
    """Pide la elección que está en st.pendiente (a quién, qué número, qué poder...)."""
    st = game.board.state
    st.turno_n += 1
    st.subfase = "Objetivo"
    actor = st.pendiente.get("actor")
    texto, privado = M.texto_objetivo(game)
    opciones = {"{}_{}".format(st.turno_n, k): v for k, v in M.opciones_objetivo(game).items()}
    markup = teclado(game.cid, "objGP", actor, opciones, columnas=1 if len(opciones) <= 4 else 2)
    jugador = game.playerlist.get(actor)
    llamado = "\n👉 {}".format(player_call(jugador)) if jugador else ""
    relato = _relato(st)
    enviado = None
    if privado:
        try:
            enviado = await bot.send_message(destino_privado(game, actor), texto,
                                             parse_mode=ParseMode.MARKDOWN, reply_markup=markup)
            await enviar(bot, game.cid, (relato + "\n\n" if relato else "") + "🤫 {} elige en privado...{}".format(
                M.nombre_corto(M.sujeto(st)), llamado))
        except Exception as e:
            logger.warning("GP pedir_objetivo privado: %s", e)
    if enviado is None:
        texto = (relato + "\n\n" if relato else "") + texto + llamado
        await enviar(bot, game.cid, texto, reply_markup=markup)
    await save(bot, game.cid)


async def callback_objetivo(update: Update, context: CallbackContext):
    bot = context.bot
    callback = update.callback_query
    try:
        cid, data_key, uid = _parse(callback.data, "objGP")
        game = _juego(cid)
        if not game:
            return await _responder(callback)
        clave = _validar_turno(game, data_key, uid, callback.from_user.id, "Objetivo")
        st = game.board.state
        if clave is None or clave not in M.opciones_objetivo(game):
            return await _responder(callback, "Ese botón ya no vale.")
        await _responder(callback)
        await _quitar_botones(bot, callback)
        st.subfase = "Procesando"
        await save(bot, cid)
        lanzar(clave_tarea(cid), _tarea_segura(bot, game, procesar_objetivo(bot, game, clave)))
    except Exception as e:
        await bot.send_message(ADMIN[0], "GP callback_objetivo error: {}".format(e))


async def procesar_objetivo(bot, game, clave):
    sigue = M.aplicar_objetivo(game, clave)
    if sigue == "previa":
        await continuar_previas(bot, game)
    elif sigue == "objetivo":
        await pedir_objetivo(bot, game)
    elif sigue == "accion":
        await seguir_turno(bot, game)
    else:
        await terminar_turno(bot, game)


async def seguir_turno(bot, game):
    """Después de un poder de "antes de moverse": el mismo corredor sigue su turno."""
    st = game.board.state
    if M.carrera_terminada(st):
        await terminar_carrera(bot, game)
    elif not M.en_carrera(M.corredor_actual(st)):
        await terminar_turno(bot, game)
    else:
        await enviar_prompt_turno(bot, game)


async def callback_post_tirada(update: Update, context: CallbackContext):
    bot = context.bot
    callback = update.callback_query
    try:
        cid, data_key, uid = _parse(callback.data, "postGP")
        game = _juego(cid)
        if not game:
            return await _responder(callback)
        opcion = _validar_turno(game, data_key, uid, callback.from_user.id, "PostTirada")
        st = game.board.state
        if opcion is None or opcion not in M.opciones_post_tirada(game):
            return await _responder(callback, "Ese botón ya no vale.")
        await _responder(callback)
        await _quitar_botones(bot, callback)
        st.subfase = "Procesando"
        await save(bot, cid)
        lanzar(clave_tarea(cid), _tarea_segura(bot, game, procesar_post(bot, game, opcion)))
    except Exception as e:
        await bot.send_message(ADMIN[0], "GP callback_post_tirada error: {}".format(e))


async def _tarea_segura(bot, game, coro):
    try:
        await coro
    except Exception as e:
        logger.exception("GP tarea error")
        st = game.board.state
        st.subfase = "Accion"
        await bot.send_message(ADMIN[0], "GP tarea error en {}: {}".format(game.cid, e))
        await enviar(bot, game.cid, "⚠️ Hubo un problema procesando el turno. Usen /call para retomarlo.", parse_mode=None)


async def tirar(bot, game):
    """Tira el dado de Telegram, repite los 6 si está el Aguafiestas y aplica el Paralizador."""
    valor = await tirar_dado(bot, game.cid)
    for _ in range(M.MAX_REPETICIONES_SEIS):
        if valor != 6 or not M.hay_aguafiestas(game.board.state):
            break
        M.repetir_seis(game)
        valor = await tirar_dado(bot, game.cid)
    return M.ajustar_dado(game, valor)


async def nueva_tirada(bot, game):
    """Tira (o vuelve a tirar) el dado del turno."""
    st = game.board.state
    c = M.corredor_actual(st)
    if M.tiene(st, c, "maestro"):
        M.tirar_seis(game)
        return
    st.pendiente["dado"] = await tirar(bot, game)
    if M.critico_fuerza(game):
        st.pendiente["dado"] = await tirar(bot, game)


async def procesar_accion(bot, game, accion):
    st = game.board.state
    tipo = M.tipo_accion(accion)
    if tipo == "tirada":
        prediccion = int(accion[4:]) if accion.startswith("adiv") else None
        st.pendiente["prediccion"] = prediccion
        if prediccion is not None:
            st.log.append("🔮 {} predice un {}.".format(M.nombre(game, M.corredor_actual(st)), prediccion))
        await nueva_tirada(bot, game)
        await decidir_o_mover(bot, game)
    elif tipo == "previa":
        M.accion_previa(game, accion)
        await seguir_turno(bot, game)
    else:
        M.accion_alternativa(game, accion)
        await terminar_turno(bot, game)


async def decidir_o_mover(bot, game):
    st = game.board.state
    if M.carrera_terminada(st):
        await terminar_turno(bot, game)
        return
    opciones = M.opciones_post_tirada(game)
    if not opciones:
        M.resolver_tirada(game)
        await terminar_turno(bot, game)
        return
    c = M.corredor_actual(st)
    st.subfase = "PostTirada"
    st.turno_n += 1
    p = st.pendiente
    if p.get("dado") is None:
        texto = "🎲 {} sacó {}. ¿Con qué número se queda?".format(
            M.nombre_corto(c), " ".join(str(d) for d in p.get("dados6", [])))
    else:
        texto = "🎲 {} sacó *{}*. ¿Qué hacés?".format(M.nombre_corto(c), p["dado"])
    relato = _relato(st)
    if relato:
        texto = relato + "\n\n" + texto
    teclas = {"{}_{}".format(st.turno_n, k): v for k, v in opciones.items()}
    await enviar(bot, game.cid, texto, reply_markup=teclado(game.cid, "postGP", c.uid, teclas, columnas=2))
    await save(bot, game.cid)


async def procesar_post(bot, game, opcion):
    st = game.board.state
    if opcion.startswith("m") and opcion[1:].isdigit():
        M.elegir_maestro(game, int(opcion[1:]))
        await decidir_o_mover(bot, game)
        return
    if opcion in ("rep_apostador", "rep_ilusionista"):
        M.registrar_repeticion(game, opcion)
        if M.carrera_terminada(st):
            await terminar_turno(bot, game)
            return
        await nueva_tirada(bot, game)
        await decidir_o_mover(bot, game)
        return
    if opcion == "seguir":
        if M.presumido_sigue(game, await tirar(bot, game)):
            await decidir_o_mover(bot, game)
            return
        M.resolver_tirada(game)
        await terminar_turno(bot, game)
        return
    M.resolver_tirada(game, doble=(opcion == "cohete"))
    await terminar_turno(bot, game)


async def terminar_turno(bot, game):
    st = game.board.state
    extra = M.fin_de_turno(game)
    if M.carrera_terminada(st):
        await terminar_carrera(bot, game)
        return
    if not extra:
        M.avanzar_turno(game)
    await proximo_turno(bot, game)


# ---------------------------------------------------------------------------
# Fin de carrera y de partida
# ---------------------------------------------------------------------------

async def terminar_carrera(bot, game):
    st = game.board.state
    if st.fase_actual != "Carrera":
        return
    st.subfase = None
    relato = _relato(st)
    resultado = M.puntuar_carrera(game)
    tabla = "\n".join("• {}: *{}*".format(p.name, p.puntos)
                      for p in sorted(game.player_sequence, key=lambda p: -p.puntos))
    await enviar_pista(bot, game, relato, resultado + "\n\n📊 *Puntos:*\n" + tabla)

    for p in game.player_sequence:
        p.usados += p.elegidos
        p.elegidos = []

    if st.carrera >= CANTIDAD_CARRERAS:
        await finalizar_juego(bot, game)
        return
    st.carrera += 1
    await iniciar_eleccion(bot, game)


async def finalizar_juego(bot, game):
    st = game.board.state
    st.fase_actual = "Finalizado"
    ganadores = M.ganadores(game)
    st.ganadores_uids = [p.uid for p in ganadores]
    await save(bot, game.cid)
    nombres = " y ".join(p.name for p in ganadores)
    await enviar(bot, game.cid, "🏆🎉 *¡{} {} el Gran Premio Arcano!* 🎉🏆".format(
        nombres, "ganan" if len(ganadores) > 1 else "gana"))
    await bot.send_message(
        game.cid, "¿Quieren seguir jugando?",
        reply_markup=teclado(game.cid, "chooseendGP", 1, {
            "Nuevo": "Nueva partida con nuevos jugadores",
            "Mismos": "Misma partida, mismos jugadores",
        })
    )


async def callback_finish_game_buttons_gp(update: Update, context: CallbackContext):
    bot = context.bot
    callback = update.callback_query
    try:
        cid, opcion, uid = _parse(callback.data, "chooseendGP")
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
        await bot.send_message(ADMIN[0], "GP callback_finish_game_buttons_gp error: {}".format(e))


# ---------------------------------------------------------------------------
# Recordatorio (/call)
# ---------------------------------------------------------------------------

async def recordar(bot, game):
    st = game.board.state
    fase = st.fase_actual
    if fase == "Configurando":
        await preguntar_reparto(bot, game)
    elif fase == "Draft":
        await pedir_pick(bot, game)
    elif fase == "Eleccion":
        k = game.corredores_por_carrera()
        faltan = [p for p in game.player_sequence if len(p.elegidos) < k]
        await enviar(bot, game.cid, "⏳ Esperando que elijan en privado: {}".format(
            ", ".join(player_call(p) for p in faltan)))
        for p in faltan:
            await pedir_eleccion(bot, game, p)
    elif fase == "Carrera":
        if en_curso(clave_tarea(game.cid)):
            await enviar(bot, game.cid, "⏳ Se está resolviendo el turno...", parse_mode=None)
            return
        if st.subfase == "PostTirada" and (st.pendiente.get("dado") is not None or st.pendiente.get("dados6")):
            st.subfase = "Procesando"
            lanzar(clave_tarea(game.cid), _tarea_segura(bot, game, decidir_o_mover(bot, game)))
        elif st.pendiente.get("objetivo"):
            st.subfase = "Procesando"
            lanzar(clave_tarea(game.cid), _tarea_segura(bot, game, pedir_objetivo(bot, game)))
        else:
            st.turno_n += 1
            st.subfase = "Procesando"
            lanzar(clave_tarea(game.cid), _tarea_segura(bot, game, enviar_prompt_turno(
                bot, game, relato="⏰ ¡Les recuerdo que la carrera sigue!")))
    elif fase == "Largando":
        if not en_curso(clave_tarea(game.cid)):
            lanzar(clave_tarea(game.cid), _tarea_segura(bot, game, revelar_y_largar(bot, game)))
