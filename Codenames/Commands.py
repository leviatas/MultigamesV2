import logging as log
import os
import urllib.parse

import psycopg
import Codenames.Controller as CodenamesController
from Utils import get_game, save, player_call, simple_choose_buttons

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext
import GamesController
from Constants.Config import ADMIN

import re

log.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s Codenames',
    level=log.INFO)
logger = log.getLogger(__name__)

urllib.parse.uses_netloc.append("postgres")
url = urllib.parse.urlparse(os.environ["DATABASE_URL"])


async def command_hint(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args

    try:
        uid = update.message.from_user.id
        cid = update.message.chat_id
    except Exception:
        return

    # /hint must be used in private chat
    if update.effective_message.chat.type in ['group', 'supergroup']:
        try:
            await bot.delete_message(cid, update.message.message_id)
        except Exception:
            pass
        await bot.send_message(uid, "Debes usar /hint en privado, no en el grupo.")
        return

    if len(args) < 2:
        await bot.send_message(uid, "Uso: /hint PALABRA NUMERO  (ej: /hint ANIMAL 3)")
        return

    word = args[0]
    try:
        number = int(args[1])
    except ValueError:
        await bot.send_message(uid, "El segundo argumento debe ser un número entero.")
        return

    if not (0 <= number <= 9):
        await bot.send_message(uid, "El número debe ser entre 0 y 9.")
        return

    # Load all Codenames games from DB to memory
    try:
        conn = psycopg.connect(
            dbname=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port,
        )
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM games g WHERE g.tipojuego = 'Codenames'")
        if cursor.rowcount > 0:
            for table in cursor.fetchall():
                if table[0] not in GamesController.games:
                    get_game(table[0])
        conn.close()
    except Exception as e:
        log.error(f'DB error in command_hint: {e}')

    valid_games = [
        g for g in GamesController.games.values()
        if g.tipo == "Codenames"
        and uid in g.playerlist
        and g.board is not None
        and g.is_spymaster(uid)
        and g.board.state.fase_actual in ("Turno Rojo - Pista", "Turno Azul - Pista")
    ]

    if len(valid_games) == 0:
        await bot.send_message(uid, "No hay partida donde puedas dar pista ahora.")
        return

    if len(valid_games) == 1:
        await CodenamesController.process_hint(bot, valid_games[0], uid, word, number)
        return

    # Multiple eligible games — show selection buttons
    btns = []
    for g in valid_games:
        datos = f"{g.cid}*choosegamehintCN*{word}_{number}*{uid}"
        btns.append([InlineKeyboardButton(g.groupName, callback_data=datos)])
    datos = f"-1*choosegamehintCN*cancel*{uid}"
    btns.append([InlineKeyboardButton("Cancelar", callback_data=datos)])
    await bot.send_message(uid, "¿En qué grupo quieres dar la pista?", reply_markup=InlineKeyboardMarkup(btns))


async def callback_choose_game_hint_cn(update: Update, context: CallbackContext):
    bot = context.bot
    callback = update.callback_query
    try:
        regex = re.search(r"(-?[0-9]*)\*choosegamehintCN\*(.*)\*([0-9]*)", callback.data)
        cid_str, opcion, uid = regex.group(1), regex.group(2), int(regex.group(3))

        if cid_str == "-1":
            await bot.edit_message_text("Cancelado.", uid, callback.message.message_id)
            return

        game = get_game(int(cid_str))
        await bot.edit_message_text(f"Grupo elegido: {game.groupName}", uid, callback.message.message_id)

        parts = opcion.rsplit("_", 1)
        word = parts[0]
        number = int(parts[1])
        await CodenamesController.process_hint(bot, game, uid, word, number)
    except Exception as e:
        await bot.send_message(ADMIN[0], f'callback_choose_game_hint_cn error: {e}')


async def command_pick(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    cid = update.message.chat_id
    uid = update.message.from_user.id

    game = get_game(cid)
    if not game or game.tipo != "Codenames" or not game.board:
        return

    if len(args) < 1:
        await bot.send_message(cid, "Uso: /pick NUMERO  (ej: /pick 7)")
        return

    try:
        numero = int(args[0])
    except ValueError:
        await bot.send_message(cid, "El argumento debe ser un número entre 1 y 25.")
        return

    if numero < 1 or numero > 25:
        await bot.send_message(cid, "El número debe ser entre 1 y 25.")
        return

    team = game.board.state.turno_actual
    fase = game.board.state.fase_actual

    if fase != f"Turno {team} - Adivinar":
        await bot.send_message(cid, "No es el momento de adivinar.")
        return

    if not game.is_field_operative(uid, team):
        await bot.send_message(cid, "No eres un agente de campo del equipo activo.")
        return

    card = next((c for c in game.board.state.tablero if c["numero"] == numero), None)
    if card is None or card["revealed"]:
        await bot.send_message(cid, "Carta inválida o ya revelada.")
        return

    await CodenamesController.process_pick(bot, game, uid, numero)


async def command_endturn(update: Update, context: CallbackContext):
    bot = context.bot
    cid = update.message.chat_id
    uid = update.message.from_user.id

    game = get_game(cid)
    if not game or game.tipo != "Codenames" or not game.board:
        return

    team = game.board.state.turno_actual
    fase = game.board.state.fase_actual

    if fase != f"Turno {team} - Adivinar":
        await bot.send_message(cid, "No estás en fase de adivinar.")
        return

    if not game.is_field_operative(uid, team):
        await bot.send_message(cid, "Solo los agentes de campo pueden terminar el turno.")
        return

    await bot.send_message(
        cid,
        f"El equipo *{team}* termina su turno voluntariamente.",
        parse_mode=ParseMode.MARKDOWN,
    )
    await CodenamesController.end_turn(bot, game)


async def command_call(bot, game):
    fase = game.board.state.fase_actual
    if not fase:
        return

    if "Pista" in fase:
        team = game.board.state.turno_actual
        sm = game.get_spymaster(team)
        await bot.send_message(
            game.cid,
            f"{player_call(sm)} es tu turno de dar la pista del equipo *{team}*.\nUsa `/hint PALABRA NUMERO` en privado.",
            parse_mode=ParseMode.MARKDOWN,
        )
        await bot.send_message(sm.uid, "Es tu turno. Usa `/hint PALABRA NUMERO` aquí.", parse_mode=ParseMode.MARKDOWN)

    elif "Adivinar" in fase:
        team = game.board.state.turno_actual
        pista = game.board.state.pista_actual
        numero = game.board.state.numero_pista
        intentos = game.board.state.intentos_restantes
        await bot.send_message(
            game.cid,
            f"Equipo *{team}*: pista *{pista}* — {numero}. Intentos restantes: {intentos}.\nUsa `/pick NUMERO` o `/endturn`.",
            parse_mode=ParseMode.MARKDOWN,
        )
        await bot.send_message(game.cid, game.board.print_board(game), parse_mode=ParseMode.MARKDOWN)
