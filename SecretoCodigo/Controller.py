#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging as log
import os
import random
import re

_TXT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'txt')

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

from Utils import get_game, save, player_call, simple_choose_buttons
from Constants.Config import ADMIN
from SecretoCodigo.Boardgamebox.Game import Game
from SecretoCodigo.Boardgamebox.Board import Board
import GamesController

log.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s SecretoCodigo',
    level=log.INFO)
logger = log.getLogger(__name__)


async def init_game(bot, game):
    try:
        log.info('SecretoCodigo init_game called')
        game.shuffle_player_sequence()
        game.board.state.fase_actual = "Configurando"
        await call_dicc_buttons(bot, game)
    except Exception as e:
        await bot.send_message(game.cid, f'No se ejecuto el comando debido a: {e}')


async def call_dicc_buttons(bot, game):
    opciones_botones = {
        "original": "Español Original",
    }
    await simple_choose_buttons(
        bot, game.cid, 1234, game.cid,
        "choosediccCN",
        "¿Elige un diccionario para jugar Secreto Código?",
        opciones_botones,
    )


async def callback_finish_config_cn(update: Update, context: CallbackContext):
    bot = context.bot
    callback = update.callback_query
    try:
        regex = re.search(r"(-[0-9]*)\*choosediccCN\*(.*)\*([0-9]*)", callback.data)
        cid, opcion, uid = int(regex.group(1)), regex.group(2), int(regex.group(3))
        mensaje_edit = f"Has elegido el diccionario: {opcion}"
        try:
            await bot.edit_message_text(mensaje_edit, cid, callback.message.message_id)
        except Exception:
            await bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)

        game = get_game(cid)
        game.configs['diccionario'] = opcion
        await finish_config(bot, game)
    except Exception as e:
        await bot.send_message(ADMIN[0], f'callback_finish_config_cn error: {e}')
        await bot.send_message(ADMIN[0], callback.data)


async def finish_config(bot, game):
    log.info('SecretoCodigo finish_config called')
    opcion = game.configs.get('diccionario', 'original')
    url_palabras = os.path.join(_TXT_DIR, f'spanish-{opcion}.txt')
    with open(url_palabras, 'r') as f:
        palabras_posibles = [w.strip() for w in f.readlines() if w.strip()]

    palabras = random.sample(palabras_posibles, 25)
    game.board.state.tablero = [
        {"word": w, "tipo": None, "revealed": False, "numero": i + 1}
        for i, w in enumerate(palabras)
    ]

    if game.modo == "Cooperativo":
        await setup_duo(bot, game)
        return

    tipos = ["rojo"] * 9 + ["azul"] * 8 + ["neutral"] * 7 + ["asesino"] * 1
    random.shuffle(tipos)
    for card, tipo in zip(game.board.state.tablero, tipos):
        card["tipo"] = tipo
    game.board.state.palabras_rojo_restantes = 9
    game.board.state.palabras_azul_restantes = 8

    await assign_teams(bot, game)


async def assign_teams(bot, game):
    log.info('SecretoCodigo assign_teams called')
    mitad = len(game.player_sequence) // 2
    equipo_rojo = game.player_sequence[:mitad]
    equipo_azul = game.player_sequence[mitad:]

    game.board.state.equipo_rojo = equipo_rojo
    game.board.state.equipo_azul = equipo_azul

    for p in equipo_rojo:
        game.playerlist[p.uid].equipo = "Rojo"
    for p in equipo_azul:
        game.playerlist[p.uid].equipo = "Azul"

    spymaster_rojo = equipo_rojo[0]
    spymaster_azul = equipo_azul[0]
    game.board.state.spymaster_rojo = spymaster_rojo
    game.board.state.spymaster_azul = spymaster_azul
    game.playerlist[spymaster_rojo.uid].es_espia = True
    game.playerlist[spymaster_azul.uid].es_espia = True

    nombres_rojo = ", ".join(p.name for p in equipo_rojo)
    nombres_azul = ", ".join(p.name for p in equipo_azul)
    msg = (
        f"🔴 *Equipo Rojo*: {nombres_rojo}\n"
        f"🔵 *Equipo Azul*: {nombres_azul}\n\n"
        f"Espías — *{spymaster_rojo.name}* (Rojo), *{spymaster_azul.name}* (Azul)"
    )
    await bot.send_message(game.cid, msg, parse_mode=ParseMode.MARKDOWN)

    for sm, team in [(spymaster_rojo, "Rojo"), (spymaster_azul, "Azul")]:
        emoji = "🔴" if team == "Rojo" else "🔵"
        await bot.send_photo(
            sm.uid,
            photo=game.board.render_spymaster_image(game),
            caption=f"{emoji} Eres el espía del equipo *{team}* — todos los colores visibles",
            parse_mode=ParseMode.MARKDOWN,
        )

    await start_turn(bot, game, "Rojo")


async def start_turn(bot, game, team: str):
    log.info(f'SecretoCodigo start_turn called — equipo {team}')
    game.board.state.fase_actual = f"Turno {team} - Pista"
    game.board.state.turno_actual = team
    game.board.state.pista_actual = None
    game.board.state.numero_pista = 0
    game.board.state.intentos_restantes = 0

    spymaster = game.get_spymaster(team)
    emoji = "🔴" if team == "Rojo" else "🔵"

    caption_turno = (
        f"{emoji} Turno del equipo *{team}*.\n"
        f"Espía {player_call(spymaster)}, da tu pista en privado con:\n`/hint PALABRA NUMERO`"
    )
    await bot.send_photo(
        game.cid,
        photo=game.board.render_board_image(game),
        caption=caption_turno,
        parse_mode=ParseMode.MARKDOWN,
    )
    await bot.send_message(
        spymaster.uid,
        f"Es tu turno de espía ({team}). Usa `/hint PALABRA NUMERO` en este chat.",
        parse_mode=ParseMode.MARKDOWN,
    )
    await save(bot, game.cid)


async def setup_duo(bot, game):
    log.info('SecretoCodigo setup_duo called')
    jugadores = game.player_sequence
    jugador_a, jugador_b = jugadores[0], jugadores[1]
    game.board.state.jugador_a = jugador_a
    game.board.state.jugador_b = jugador_b

    # Layout Codenames Dúo (25 cartas):
    # 3 agentes compartidos          (verde A + verde B)
    # 6 agentes solo A               (verde A + gris B)
    # 6 agentes solo B               (gris A + verde B)
    # 1 asesino compartido           (negro A + negro B)
    # 1 asesino verde de A           (negro A + VERDE B) ← trampa: B lo ve como agente
    # 1 asesino gris  de A           (negro A + gris B)
    # 1 asesino verde de B           (VERDE A + negro B) ← trampa: A lo ve como agente
    # 1 asesino gris  de B           (gris A  + negro B)
    # 5 neutrales                    (gris A  + gris B)
    # Cada jugador ve exactamente 3 negros en su clave.
    nums = list(range(1, 26))
    random.shuffle(nums)

    shared_agents    = set(nums[0:3])
    a_agents         = set(nums[3:9])
    b_agents         = set(nums[9:15])
    shared_assassin  = nums[15]
    a_verde_assassin = nums[16]   # negro A, verde B  (trampa para B)
    a_gris_assassin  = nums[17]   # negro A, gris B
    b_verde_assassin = nums[18]   # verde A, negro B  (trampa para A)
    b_gris_assassin  = nums[19]   # gris A,  negro B
    # nums[20:25] = 5 neutrales puros

    key_a = {}
    key_b = {}
    for n in range(1, 26):
        if n in shared_agents:
            key_a[n] = "agente";  key_b[n] = "agente"
        elif n in a_agents:
            key_a[n] = "agente";  key_b[n] = "neutral"
        elif n in b_agents:
            key_a[n] = "neutral"; key_b[n] = "agente"
        elif n == shared_assassin:
            key_a[n] = "asesino"; key_b[n] = "asesino"
        elif n == a_verde_assassin:
            key_a[n] = "asesino"; key_b[n] = "agente"   # B lo ve verde → trampa
        elif n == a_gris_assassin:
            key_a[n] = "asesino"; key_b[n] = "neutral"
        elif n == b_verde_assassin:
            key_a[n] = "agente";  key_b[n] = "asesino"  # A lo ve verde → trampa
        elif n == b_gris_assassin:
            key_a[n] = "neutral"; key_b[n] = "asesino"
        else:
            key_a[n] = "neutral"; key_b[n] = "neutral"

    game.board.state.key_a = key_a
    game.board.state.key_b = key_b
    game.board.state.agentes_revelados = 0
    game.board.state.total_agentes_duo = 15
    game.board.state.pistas_restantes = 9

    await bot.send_message(
        game.cid,
        f"🤝 *Modo Dúo activado!*\nJugador A: *{jugador_a.name}*\nJugador B: *{jugador_b.name}*\n\n"
        "Cada uno recibirá su clave secreta en privado. Trabajen juntos para encontrar los 15 agentes "
        "sin tocar ninguno de los 3 asesinos, ¡antes de quedarse sin pistas!",
        parse_mode=ParseMode.MARKDOWN,
    )
    await bot.send_photo(
        jugador_a.uid,
        photo=game.board.render_key_image(game, "A"),
        caption="🟩 Tu clave (Jugador A) — verde=agente, negro=asesino, gris=neutral",
    )
    await bot.send_photo(
        jugador_b.uid,
        photo=game.board.render_key_image(game, "B"),
        caption="🟩 Tu clave (Jugador B) — verde=agente, negro=asesino, gris=neutral",
    )

    await start_turn_duo(bot, game, "A")


async def start_turn_duo(bot, game, dador_label: str):
    log.info(f'SecretoCodigo start_turn_duo called — dador {dador_label}')
    st = game.board.state
    st.fase_actual = f"Duo {dador_label} - Pista"
    st.dador_actual = dador_label
    st.pista_actual = None
    st.numero_pista = 0
    st.intentos_restantes = 0

    dador = game.get_player_by_label(dador_label)
    receptor = game.get_player_by_label(game.get_other_player_label(dador_label))

    await bot.send_photo(
        game.cid,
        photo=game.board.render_duo_board_image(game),
        caption=(
            f"🗣️ Turno de pista del Jugador *{dador.name}* (rol {dador_label}).\n"
            f"{player_call(dador)}, da tu pista en privado con `/hint PALABRA NUMERO`."
        ),
        parse_mode=ParseMode.MARKDOWN,
    )
    await bot.send_message(dador.uid, "Es tu turno de dar pista. Usa `/hint PALABRA NUMERO` aquí.", parse_mode=ParseMode.MARKDOWN)
    await save(bot, game.cid)


async def process_hint_duo(bot, game, uid, word: str, number: int):
    log.info('SecretoCodigo process_hint_duo called')
    st = game.board.state
    fase = st.fase_actual
    dador_label = st.dador_actual
    dador = game.get_player_by_label(dador_label)
    receptor = game.get_player_by_label(game.get_other_player_label(dador_label))

    if fase != f"Duo {dador_label} - Pista":
        await bot.send_message(uid, "No es el momento de dar pista.")
        return
    if not dador or dador.uid != uid:
        await bot.send_message(uid, "No eres quien debe dar la pista ahora.")
        return
    if " " in word:
        await bot.send_message(uid, "La pista debe ser una sola palabra sin espacios.")
        return
    if not (0 <= number <= 9):
        await bot.send_message(uid, "El número debe ser entre 0 y 9.")
        return

    st.pista_actual = word.upper()
    st.numero_pista = number
    st.intentos_restantes = number + 1
    st.fase_actual = f"Duo {dador_label} - Adivinar"

    await bot.send_photo(
        game.cid,
        photo=game.board.render_duo_board_image(game),
        caption=(
            f"💬 Pista de *{dador.name}*: *{word.upper()}* — {number}\n"
            f"{player_call(receptor)}, usa `/pick NUMERO` para adivinar (en el grupo). "
            f"Hasta *{number + 1}* intentos o `/endturn` para pasar."
        ),
        parse_mode=ParseMode.MARKDOWN,
    )
    await save(bot, game.cid)


async def process_pick_duo(bot, game, uid, numero: int):
    log.info('Codenames process_pick_duo called')
    st = game.board.state

    card = next((c for c in st.tablero if c["numero"] == numero), None)
    card["revealed"] = True
    word = card["word"]

    tipo_a = st.key_a[numero]
    tipo_b = st.key_b[numero]
    tipo_hinter_pre = tipo_a if st.dador_actual == "A" else tipo_b

    # Si es asesino en CUALQUIERA de las dos claves → derrota inmediata
    # Esto incluye la trampa: asesino de B que A ve como agente (verde)
    if tipo_a == "asesino" or tipo_b == "asesino":
        card["tipo"] = "asesino"
        await bot.send_message(
            game.cid,
            f"💀 *¡ASESINO!* *{word.upper()}* era un asesino. El equipo ha perdido.",
            parse_mode=ParseMode.MARKDOWN,
        )
        await end_game_duo(bot, game, victoria=False, razon="asesino")
        return

    # Resultado según la clave de quien da la pista
    tipo_hinter = tipo_hinter_pre
    emoji_map = {"agente": "🟩", "neutral": "⬜"}
    await bot.send_message(
        game.cid,
        f"Carta {numero} revelada: *{word.upper()}* {emoji_map.get(tipo_hinter, '⬜')}",
        parse_mode=ParseMode.MARKDOWN,
    )

    if tipo_hinter == "agente":
        card["tipo"] = "agente"
        st.agentes_revelados += 1
        if st.agentes_revelados >= st.total_agentes_duo:
            await end_game_duo(bot, game, victoria=True, razon="agentes")
            return
        st.intentos_restantes -= 1
        if st.intentos_restantes <= 0:
            await bot.send_message(game.cid, "Se agotaron los intentos. Cambio de turno.", parse_mode=ParseMode.MARKDOWN)
            await end_turn_duo(bot, game)
        else:
            await bot.send_photo(
                game.cid,
                photo=game.board.render_duo_board_image(game),
                caption=f"✅ *¡Correcto!* Agentes encontrados: {st.agentes_revelados}/{st.total_agentes_duo}. Intentos restantes: {st.intentos_restantes}",
                parse_mode=ParseMode.MARKDOWN,
            )
            await save(bot, game.cid)
    else:
        card["tipo"] = "neutral"
        st.pistas_restantes -= 1
        await bot.send_message(
            game.cid,
            f"❌ Esa carta no era un agente. Pistas restantes: {st.pistas_restantes}. Cambio de turno.",
            parse_mode=ParseMode.MARKDOWN,
        )
        if st.pistas_restantes <= 0:
            await end_game_duo(bot, game, victoria=False, razon="sin_pistas")
            return
        await end_turn_duo(bot, game)


async def end_turn_duo(bot, game):
    st = game.board.state
    next_label = game.get_other_player_label(st.dador_actual)
    await bot.send_message(
        game.cid,
        f"--- Turno de pista para *{game.get_player_by_label(next_label).name}* ---",
        parse_mode=ParseMode.MARKDOWN,
    )
    await start_turn_duo(bot, game, next_label)


async def end_game_duo(bot, game, victoria: bool, razon: str):
    st = game.board.state
    st.fase_actual = "Finalizado"
    await save(bot, game.cid)

    if victoria:
        msg = f"🎉 ¡Equipo ganador! Encontraron los {st.total_agentes_duo} agentes trabajando juntos."
    elif razon == "asesino":
        msg = "💀 Derrota: tocaron al asesino."
    else:
        msg = "⌛ Derrota: se acabaron las pistas antes de encontrar a todos los agentes."

    await bot.send_message(game.cid, msg, parse_mode=ParseMode.MARKDOWN)
    await bot.send_message(game.cid, _reveal_full_board_duo(game), parse_mode=ParseMode.MARKDOWN)
    await continue_playing(bot, game)


def _reveal_full_board_duo(game) -> str:
    st = game.board.state
    emoji_map = {"agente": "🟩", "neutral": "⬜", "asesino": "💀"}
    lines = []
    for i, card in enumerate(st.tablero):
        n = card["numero"]
        tipo_a = st.key_a[n]
        tipo_b = st.key_b[n]
        marker = "✅" if card["revealed"] else "  "
        lines.append(f"{marker}{card['word'].upper()} — A:{emoji_map[tipo_a]} B:{emoji_map[tipo_b]}")
        if (i + 1) % 5 == 0:
            lines.append("")
    return "*Tablero Final (vista A / vista B):*\n" + "\n".join(lines)


async def process_hint(bot, game, spymaster_uid, word: str, number: int):
    log.info('Codenames process_hint called')
    fase = game.board.state.fase_actual
    team = game.board.state.turno_actual
    spymaster = game.get_spymaster(team)

    if f"Turno {team} - Pista" != fase:
        await bot.send_message(spymaster_uid, "No es el momento de dar pista.")
        return
    if not spymaster or spymaster.uid != spymaster_uid:
        await bot.send_message(spymaster_uid, "No eres el espía activo.")
        return
    if " " in word:
        await bot.send_message(spymaster_uid, "La pista debe ser una sola palabra sin espacios.")
        return
    if not (0 <= number <= 9):
        await bot.send_message(spymaster_uid, "El número debe ser entre 0 y 9.")
        return

    game.board.state.pista_actual = word.upper()
    game.board.state.numero_pista = number
    game.board.state.intentos_restantes = number + 1
    game.board.state.fase_actual = f"Turno {team} - Adivinar"

    field_mentions = " ".join(
        player_call(p)
        for p in game.get_team_players(team)
        if not game.is_spymaster(p.uid)
    )
    caption_pista = (
        f"💬 Pista del espía *{team}*: *{word.upper()}* — {number}\n"
        f"{field_mentions} usen `/pick NUMERO` para elegir una carta.\n"
        f"Hasta *{number + 1}* intentos o `/endturn` para pasar."
    )
    await bot.send_photo(
        game.cid,
        photo=game.board.render_board_image(game),
        caption=caption_pista,
        parse_mode=ParseMode.MARKDOWN,
    )
    await save(bot, game.cid)


async def process_pick(bot, game, uid, numero: int):
    log.info('Codenames process_pick called')
    card = next((c for c in game.board.state.tablero if c["numero"] == numero), None)
    card["revealed"] = True
    tipo = card["tipo"]
    word = card["word"]
    team = game.board.state.turno_actual

    emoji_map = {"rojo": "🟥", "azul": "🟦", "neutral": "⬜", "asesino": "💀"}
    await bot.send_message(
        game.cid,
        f"Carta {numero} revelada: *{word.upper()}* {emoji_map[tipo]}",
        parse_mode=ParseMode.MARKDOWN,
    )

    if tipo == "asesino":
        perdedor = team
        ganador = "Azul" if team == "Rojo" else "Rojo"
        await bot.send_message(
            game.cid,
            f"💀 *¡ASESINO!* El equipo *{perdedor}* tocó al asesino. ¡Gana el equipo *{ganador}*!",
            parse_mode=ParseMode.MARKDOWN,
        )
        await end_game(bot, game, winner=ganador, reason="asesino")
        return

    if tipo == "rojo":
        game.board.state.palabras_rojo_restantes -= 1
    elif tipo == "azul":
        game.board.state.palabras_azul_restantes -= 1

    winner = await check_win(bot, game)
    if winner:
        return

    if tipo == team.lower():
        game.board.state.intentos_restantes -= 1
        if game.board.state.intentos_restantes <= 0:
            await bot.send_message(game.cid, "Se agotaron los intentos. Fin del turno.", parse_mode=ParseMode.MARKDOWN)
            await end_turn(bot, game)
        else:
            await bot.send_photo(
                game.cid,
                photo=game.board.render_board_image(game),
                caption=f"✅ *¡Correcto!* Intentos restantes: {game.board.state.intentos_restantes}",
                parse_mode=ParseMode.MARKDOWN,
            )
            await save(bot, game.cid)
    else:
        await bot.send_message(
            game.cid,
            f"❌ Esa carta no era del equipo *{team}*. Fin del turno.",
            parse_mode=ParseMode.MARKDOWN,
        )
        await end_turn(bot, game)


async def check_win(bot, game):
    if game.board.state.palabras_rojo_restantes == 0:
        await end_game(bot, game, winner="Rojo", reason="palabras")
        return "Rojo"
    if game.board.state.palabras_azul_restantes == 0:
        await end_game(bot, game, winner="Azul", reason="palabras")
        return "Azul"
    return None


async def end_turn(bot, game):
    next_team = "Azul" if game.board.state.turno_actual == "Rojo" else "Rojo"
    await bot.send_message(
        game.cid,
        f"--- Turno del equipo *{next_team}* ---",
        parse_mode=ParseMode.MARKDOWN,
    )
    await start_turn(bot, game, next_team)


async def end_game(bot, game, winner: str, reason: str):
    game.board.state.fase_actual = "Finalizado"
    await save(bot, game.cid)

    emoji = "🔴" if winner == "Rojo" else "🔵"
    motivo = "tocó al *ASESINO* 💀" if reason == "asesino" else "reveló todas sus palabras"
    perdedor = "Azul" if winner == "Rojo" else "Rojo"

    await bot.send_message(
        game.cid,
        f"{emoji} ¡El equipo *{winner}* ha GANADO porque el equipo *{perdedor}* {motivo}!",
        parse_mode=ParseMode.MARKDOWN,
    )
    await bot.send_message(game.cid, _reveal_full_board(game), parse_mode=ParseMode.MARKDOWN)
    await continue_playing(bot, game)


def _reveal_full_board(game) -> str:
    emoji_map = {"rojo": "🟥", "azul": "🟦", "neutral": "⬜", "asesino": "💀"}
    lines = []
    for i, card in enumerate(game.board.state.tablero):
        marker = "✅" if card["revealed"] else "  "
        lines.append(f"{marker}{emoji_map[card['tipo']]} {card['word'].upper()}")
        if (i + 1) % 5 == 0:
            lines.append("")
    return "*Tablero Final:*\n" + "\n".join(lines)


async def continue_playing(bot, game):
    opciones_botones = {
        "Nuevo": "Nuevo partido con nuevos jugadores",
        "Mismo Diccionario": "Mismo diccionario, mismos jugadores",
    }
    await simple_choose_buttons(
        bot, game.cid, 1, game.cid,
        "chooseendCN",
        "¿Quieres continuar jugando?",
        opciones_botones,
    )


async def callback_finish_game_buttons_cn(update: Update, context: CallbackContext):
    bot = context.bot
    callback = update.callback_query
    try:
        regex = re.search(r"(-[0-9]*)\*chooseendCN\*(.*)\*([0-9]*)", callback.data)
        cid, opcion, uid = int(regex.group(1)), regex.group(2), int(regex.group(3))
        mensaje_edit = f"Has elegido: {opcion}"
        try:
            await bot.edit_message_text(mensaje_edit, cid, callback.message.message_id)
        except Exception:
            await bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)

        game = get_game(cid)
        groupName = game.groupName
        tipo = game.tipo
        modo = game.modo
        dicc = game.configs.get('diccionario', 'original')
        players = game.playerlist.copy()

        new_game = Game(cid, uid, groupName, tipo, modo)
        GamesController.games[cid] = new_game

        if opcion == "Nuevo":
            await bot.send_message(
                cid,
                "Cada jugador puede unirse con /join. El iniciador puede escribir /startgame cuando todos estén listos.",
            )
            return

        new_game.playerlist = players
        new_game.board = None
        new_game.create_board()
        new_game.player_sequence = []
        new_game.shuffle_player_sequence()
        new_game.configs['diccionario'] = dicc
        await finish_config(bot, new_game)
    except Exception as e:
        await bot.send_message(ADMIN[0], f'callback_finish_game_buttons_cn error: {e}')
        await bot.send_message(ADMIN[0], callback.data)


async def myturn_message(game, uid) -> str:
    fase = game.board.state.fase_actual
    group = game.group_link_name()

    if game.modo == "Cooperativo":
        st = game.board.state
        if not st.dador_actual:
            return None
        dador = game.get_player_by_label(st.dador_actual)
        receptor = game.get_player_by_label(game.get_other_player_label(st.dador_actual))
        if "Pista" in fase and dador and dador.uid == uid:
            return f"Partida {group}: es tu turno de dar pista. Usa `/hint PALABRA NUMERO`"
        if "Adivinar" in fase and receptor and receptor.uid == uid:
            return f"Partida {group}: debes adivinar. Pista: *{st.pista_actual}* — {st.numero_pista}. Usa `/pick NUMERO`"
        return None

    sm_r = game.board.state.spymaster_rojo
    sm_a = game.board.state.spymaster_azul

    if fase == "Turno Rojo - Pista" and sm_r and sm_r.uid == uid:
        return f"Partida {group}: es tu turno de dar pista roja. Usa `/hint PALABRA NUMERO`"
    if fase == "Turno Azul - Pista" and sm_a and sm_a.uid == uid:
        return f"Partida {group}: es tu turno de dar pista azul. Usa `/hint PALABRA NUMERO`"
    if fase in ("Turno Rojo - Adivinar", "Turno Azul - Adivinar"):
        team = "Rojo" if "Rojo" in fase else "Azul"
        if game.is_field_operative(uid, team):
            pista = game.board.state.pista_actual
            numero = game.board.state.numero_pista
            return f"Partida {group}: equipo {team} debe adivinar. Pista: *{pista}* — {numero}. Usa `/pick NUMERO`"
    return None
