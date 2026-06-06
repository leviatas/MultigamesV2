#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging as log
import random
import re

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

from Utils import get_game, save, player_call, simple_choose_buttons
from Constants.Config import ADMIN
from Codenames.Boardgamebox.Game import Game
from Codenames.Boardgamebox.Board import Board
import GamesController

log.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s Codenames',
    level=log.INFO)
logger = log.getLogger(__name__)


async def init_game(bot, game):
    try:
        log.info('Codenames init_game called')
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
        "¿Elige un diccionario para jugar Codenames?",
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
    log.info('Codenames finish_config called')
    opcion = game.configs.get('diccionario', 'original')
    url_palabras = f'/Codenames/txt/spanish-{opcion}.txt'
    with open(url_palabras, 'r') as f:
        palabras_posibles = [w.strip() for w in f.readlines() if w.strip()]

    palabras = random.sample(palabras_posibles, 25)

    tipos = ["rojo"] * 9 + ["azul"] * 8 + ["neutral"] * 7 + ["asesino"] * 1
    random.shuffle(tipos)

    game.board.state.tablero = [
        {"word": w, "tipo": t, "revealed": False, "numero": i + 1}
        for i, (w, t) in enumerate(zip(palabras, tipos))
    ]
    game.board.state.palabras_rojo_restantes = 9
    game.board.state.palabras_azul_restantes = 8

    await assign_teams(bot, game)


async def assign_teams(bot, game):
    log.info('Codenames assign_teams called')
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

    tablero_espia = game.board.print_spymaster_board(game)
    for sm, team in [(spymaster_rojo, "Rojo"), (spymaster_azul, "Azul")]:
        emoji = "🔴" if team == "Rojo" else "🔵"
        await bot.send_message(
            sm.uid,
            f"{emoji} Eres el espía del equipo *{team}*\n\n{tablero_espia}",
            parse_mode=ParseMode.MARKDOWN,
        )

    await start_turn(bot, game, "Rojo")


async def start_turn(bot, game, team: str):
    log.info(f'Codenames start_turn called — equipo {team}')
    game.board.state.fase_actual = f"Turno {team} - Pista"
    game.board.state.turno_actual = team
    game.board.state.pista_actual = None
    game.board.state.numero_pista = 0
    game.board.state.intentos_restantes = 0

    spymaster = game.get_spymaster(team)
    emoji = "🔴" if team == "Rojo" else "🔵"

    await bot.send_message(game.cid, game.board.print_board(game), parse_mode=ParseMode.MARKDOWN)
    await bot.send_message(
        game.cid,
        f"{emoji} Turno del equipo *{team}*.\n"
        f"Espía {player_call(spymaster)}, da tu pista en privado con:\n`/hint PALABRA NUMERO`",
        parse_mode=ParseMode.MARKDOWN,
    )
    await bot.send_message(
        spymaster.uid,
        f"Es tu turno de espía ({team}). Usa `/hint PALABRA NUMERO` en este chat.",
        parse_mode=ParseMode.MARKDOWN,
    )
    await save(bot, game.cid)


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
    await bot.send_message(
        game.cid,
        f"💬 Pista del espía *{team}*: *{word.upper()}* — {number}\n"
        f"{field_mentions} usen `/pick NUMERO` para elegir una carta.\n"
        f"Hasta *{number + 1}* intentos o `/endturn` para pasar.",
        parse_mode=ParseMode.MARKDOWN,
    )
    await bot.send_message(game.cid, game.board.print_board(game), parse_mode=ParseMode.MARKDOWN)
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
            await bot.send_message(
                game.cid,
                f"✅ *¡Correcto!* Intentos restantes: {game.board.state.intentos_restantes}\n"
                + game.board.print_board(game),
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
    sm_r = game.board.state.spymaster_rojo
    sm_a = game.board.state.spymaster_azul
    group = game.group_link_name()

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
