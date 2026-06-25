#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging as log
import random
import re

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

from Utils import get_game, save, simple_choose_buttons, player_call
from Constants.Config import ADMIN
from PuertoBanana.Boardgamebox.Game import Game
from PuertoBanana.Boardgamebox.Board import BANANAS_VICTORIA

import GamesController

log.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=log.INFO)
logger = log.getLogger(__name__)


async def init_game(bot, game):
    try:
        log.info("PuertoBanana init_game called")
        game.shuffle_player_sequence()
        await bot.send_message(
            game.cid,
            "🍌 *¡Puerto Banana ha comenzado!*\n\n"
            "Todos arrancan con *10 bananas*. Gana el primero en llegar a "
            f"*{BANANAS_VICTORIA}*.\n"
            "Usá `/info` en cualquier momento para ver tu cantidad en privado.",
            parse_mode=ParseMode.MARKDOWN
        )
        await start_round(bot, game)
    except Exception as e:
        logger.error(f"PuertoBanana init_game error: {e}")
        await bot.send_message(ADMIN[0], f"PuertoBanana init_game error: {e}")
        raise


async def start_round(bot, game):
    st = game.board.state
    st.fase_actual = "Pujando"
    st.last_votes = {}
    st.pozo_actual = max(player.bananas for player in game.player_sequence)

    await bot.send_message(
        game.cid,
        f"🍌 *Ronda {st.ronda}* — El pozo es de *{st.pozo_actual}* bananas.\n"
        "Cada jugador debe pujar en privado con `/puja CANTIDAD`.",
        parse_mode=ParseMode.MARKDOWN
    )
    for player in game.player_sequence:
        await bot.send_message(
            player.uid,
            f"🍌 Partida *{game.groupName}* — Ronda {st.ronda}.\n"
            f"El pozo es de *{st.pozo_actual}* bananas.\n"
            "Hacé tu puja secreta con `/puja CANTIDAD` (no estás limitado por lo que tenés).",
            parse_mode=ParseMode.MARKDOWN
        )
    await save(bot, game.cid)


async def resolve_round(bot, game):
    st = game.board.state
    pujas = st.last_votes

    pujas_ordenadas = sorted(pujas.items(), key=lambda item: item[1], reverse=True)
    reveal = "\n".join(
        f"• {game.playerlist[uid].name}: *{monto}* bananas" for uid, monto in pujas_ordenadas
    )
    await bot.send_message(
        game.cid,
        f"🍌 *Todos pujaron.* Así quedaron las pujas:\n{reveal}",
        parse_mode=ParseMode.MARKDOWN
    )

    mayor_puja = max(pujas.values())
    candidatos_ganador = [uid for uid, monto in pujas.items() if monto == mayor_puja]
    ganador_uid = random.choice(candidatos_ganador)

    restantes = {uid: monto for uid, monto in pujas.items() if uid != ganador_uid}
    segunda_puja = max(restantes.values()) if restantes else mayor_puja
    candidatos_segundo = [uid for uid, monto in restantes.items() if monto == segunda_puja] if restantes else []
    segundo_uid = random.choice(candidatos_segundo) if candidatos_segundo else None

    diferencia = mayor_puja - segunda_puja
    ganador = game.playerlist[ganador_uid]
    pozo = st.pozo_actual

    detalle = (
        f"🍌 *Resultado de la ronda {st.ronda}:*\n"
        f"{player_call(ganador)} pujó más alto y se lleva el pozo de *{pozo}* bananas, "
        f"debiendo pagar la diferencia de *{diferencia}* bananas al segundo mejor postor.\n"
    )

    if ganador.bananas + pozo >= diferencia:
        ganador.bananas = ganador.bananas + pozo - diferencia
        ganador.eliminado_ronda = False
        if segundo_uid is not None:
            segundo = game.playerlist[segundo_uid]
            segundo.bananas += diferencia
            segundo.eliminado_ronda = False
            detalle += f"{player_call(segundo)} recibe esa diferencia."
        else:
            detalle += "Nadie más pujó, así que no paga diferencia."
    else:
        ganador.bananas = 0
        ganador.eliminado_ronda = True
        detalle += (
            f"¡Pero {player_call(ganador)} no puede pagar esa diferencia! Queda "
            "*eliminado de la ronda* y pierde todas sus bananas."
        )

    await bot.send_message(game.cid, detalle, parse_mode=ParseMode.MARKDOWN)
    await save(bot, game.cid)

    ganador_partida = next(
        (p for p in game.player_sequence if p.bananas >= BANANAS_VICTORIA),
        None
    )
    if ganador_partida is not None:
        await finish_game(bot, game, ganador_partida)
        return

    st.ronda += 1
    await start_round(bot, game)


async def finish_game(bot, game, ganador):
    st = game.board.state
    st.fase_actual = "Finalizado"
    st.ganador_uid = ganador.uid
    await save(bot, game.cid)

    resumen = "\n".join(
        f"• {p.name}: {p.bananas} bananas" for p in game.player_sequence
    )
    await bot.send_message(
        game.cid,
        f"🏆 *¡{ganador.name} ganó Puerto Banana con {ganador.bananas} bananas!*\n\n"
        f"*Resultado final:*\n{resumen}",
        parse_mode=ParseMode.MARKDOWN
    )
    await continue_playing(bot, game)


async def continue_playing(bot, game):
    opciones_botones = {
        "Nuevo": "Nuevo partido con nuevos jugadores",
        "Mismos": "Misma partida, mismos jugadores",
    }
    await simple_choose_buttons(
        bot, game.cid, 1, game.cid,
        "chooseendPB",
        "¿Quieres continuar jugando?",
        opciones_botones,
    )


async def callback_finish_game_buttons_pb(update: Update, context: CallbackContext):
    bot = context.bot
    callback = update.callback_query
    try:
        regex = re.search(r"(-[0-9]*)\*chooseendPB\*(.*)\*([0-9]*)", callback.data)
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
        players = game.playerlist.copy()

        new_game = Game(cid, uid, groupName, tipo, modo)
        GamesController.games[cid] = new_game

        if opcion == "Nuevo":
            await bot.send_message(
                cid,
                "Cada jugador puede unirse con /join. El iniciador puede escribir /startgame cuando todos estén listos.",
            )
            return

        for player in players.values():
            player.bananas = 10
            player.eliminado_ronda = False
        new_game.playerlist = players
        new_game.create_board()
        await init_game(bot, new_game)
    except Exception as e:
        await bot.send_message(ADMIN[0], f'callback_finish_game_buttons_pb error: {e}')
        await bot.send_message(ADMIN[0], callback.data)
