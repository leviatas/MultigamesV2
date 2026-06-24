#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging as log
import re

import PuertoBanana.Controller as PuertoBananaController
from Utils import get_game, save

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

import GamesController

log.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=log.INFO)
logger = log.getLogger(__name__)


def _validar_partida(game):
    return game and game.tipo == "PuertoBanana" and game.board


async def command_call(bot, game):
    """Recordatorio de quién no pujó todavía."""
    if not _validar_partida(game):
        return
    st = game.board.state
    if st.fase_actual != "Pujando":
        return
    faltantes = [p for p in game.player_sequence if p.uid not in st.last_votes]
    if not faltantes:
        return
    nombres = ", ".join(p.name for p in faltantes)
    await bot.send_message(
        game.cid,
        f"🍌 Todavía faltan pujar (en privado, con `/puja CANTIDAD`): {nombres}",
        parse_mode=ParseMode.MARKDOWN
    )


async def _aplicar_puja(bot, game, uid, monto):
    st = game.board.state
    if uid not in game.playerlist:
        await bot.send_message(uid, "No estás en esa partida de Puerto Banana.")
        return
    if st.fase_actual != "Pujando":
        await bot.send_message(uid, "No es momento de pujar.")
        return
    if uid in st.last_votes:
        await bot.send_message(uid, "Ya hiciste tu puja esta ronda.")
        return

    st.last_votes[uid] = monto
    await bot.send_message(uid, f"Tu puja de *{monto}* bananas fue registrada.", parse_mode=ParseMode.MARKDOWN)
    await bot.send_message(game.cid, f"El jugador *{game.playerlist[uid].name}* ya pujó.", parse_mode=ParseMode.MARKDOWN)
    await save(bot, game.cid)

    if len(st.last_votes) >= len(game.player_sequence):
        await PuertoBananaController.resolve_round(bot, game)


async def command_puja(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    uid = update.message.from_user.id

    if update.effective_message.chat.type in ['group', 'supergroup']:
        await bot.delete_message(update.message.chat_id, update.message.message_id)
        await bot.send_message(uid, "El comando /puja solo se puede usar en privado con el bot.")
        return

    if len(args) != 1 or not args[0].lstrip('-').isdigit():
        await bot.send_message(uid, "Uso correcto: /puja CANTIDAD. Ej: /puja 15")
        return

    monto = int(args[0])
    if monto < 0:
        await bot.send_message(uid, "No podés pujar una cantidad negativa.")
        return

    import MainController
    juegos = MainController.getGamesByTipo("PuertoBanana")
    if not juegos:
        await bot.send_message(uid, "No hay partidas de Puerto Banana en las que puedas pujar.")
        return

    candidatas = {
        cid: game for cid, game in juegos.items()
        if _validar_partida(game) and uid in game.playerlist
        and game.board.state.fase_actual == "Pujando" and uid not in game.board.state.last_votes
    }

    if not candidatas:
        await bot.send_message(uid, "No tenés ninguna puja pendiente en Puerto Banana.")
        return

    if len(candidatas) == 1:
        cid, game = next(iter(candidatas.items()))
        await _aplicar_puja(bot, game, uid, monto)
        return

    btns = []
    for cid, game in candidatas.items():
        datos = f"{cid}*choosegamepujaPB*{monto}*{uid}"
        btns.append([InlineKeyboardButton(game.groupName, callback_data=datos)])
    await bot.send_message(
        uid, "¿En cuál de estas partidas querés pujar?",
        reply_markup=InlineKeyboardMarkup(btns)
    )


async def callback_choose_game_puja(update: Update, context: CallbackContext):
    bot = context.bot
    callback = update.callback_query
    regex = re.search(r"(-[0-9]*)\*choosegamepujaPB\*(-?[0-9]*)\*([0-9]*)", callback.data)
    cid, monto, uid = int(regex.group(1)), int(regex.group(2)), int(regex.group(3))

    game = get_game(cid)
    try:
        await bot.edit_message_text(f"Has elegido la partida {game.groupName}", uid, callback.message.message_id)
    except Exception:
        pass
    await _aplicar_puja(bot, game, uid, monto)
