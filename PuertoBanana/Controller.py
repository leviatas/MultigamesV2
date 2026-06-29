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
    await bot.send_message(game.cid, game.board.print_board(game), parse_mode=ParseMode.MARKDOWN)
    for player in game.player_sequence:
        try:
            await bot.send_message(
                player.uid,
                f"🍌 Partida *{game.groupName}* — Ronda {st.ronda}.\n"
                f"El pozo es de *{st.pozo_actual}* bananas.\n"
                "Hacé tu puja secreta con `/puja CANTIDAD` (no estás limitado por lo que tenés).",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"PuertoBanana start_round no pudo avisar a {player.name} ({player.uid}): {e}")
            await bot.send_message(
                game.cid,
                f"⚠️ No pude avisarle por privado a *{player.name}*. "
                "Debe iniciar una conversación privada con el bot (`/start`) para poder pujar.",
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

    pozo = st.pozo_actual
    restantes = dict(pujas)
    detalle_lineas = [f"🍌 *Resultado de la ronda {st.ronda}:*"]

    while True:
        mayor_puja = max(restantes.values())
        candidatos_ganador = [uid for uid, monto in restantes.items() if monto == mayor_puja]

        if len(candidatos_ganador) > 1:
            empatados = [game.playerlist[uid] for uid in candidatos_ganador]
            reparto = pozo // len(empatados)
            resto = pozo % len(empatados)
            for jugador in empatados:
                jugador.bananas += reparto
                jugador.eliminado_ronda = False
            if resto:
                random.choice(empatados).bananas += resto
            nombres_empatados = ", ".join(player_call(j) for j in empatados)
            detalle_lineas.append(
                f"{nombres_empatados} empataron en la puja más alta (*{mayor_puja}*) y se "
                f"reparten el pozo de *{pozo}* bananas entre ellos, sin pagarle nada a nadie más."
            )
            break

        ganador_uid = candidatos_ganador[0]
        ganador = game.playerlist[ganador_uid]

        candidatos_resto = {uid: monto for uid, monto in restantes.items() if uid != ganador_uid}

        if not candidatos_resto:
            ganador.bananas += pozo
            ganador.eliminado_ronda = False
            detalle_lineas.append(
                f"{player_call(ganador)} es el único que queda en pie y se lleva el pozo de "
                f"*{pozo}* bananas sin pagar diferencia."
            )
            break

        segunda_puja = max(candidatos_resto.values())
        candidatos_segundo = [uid for uid, monto in candidatos_resto.items() if monto == segunda_puja]
        segundo_uid = random.choice(candidatos_segundo)
        segundo = game.playerlist[segundo_uid]
        diferencia = mayor_puja - segunda_puja

        if ganador.bananas + pozo >= diferencia:
            ganador.bananas = ganador.bananas + pozo - diferencia
            ganador.eliminado_ronda = False
            segundo.bananas += diferencia
            segundo.eliminado_ronda = False
            detalle_lineas.append(
                f"{player_call(ganador)} pujó más alto y se lleva el pozo de *{pozo}* bananas, "
                f"debiendo pagar la diferencia de *{diferencia}* bananas a {player_call(segundo)}."
            )
            break
        else:
            ganador.bananas = 0
            ganador.eliminado_ronda = True
            detalle_lineas.append(
                f"{player_call(ganador)} pujó *{mayor_puja}* pero no puede pagar la diferencia "
                f"de *{diferencia}* bananas. Queda *eliminado de la ronda* y pierde todas sus "
                "bananas."
            )
            del restantes[ganador_uid]

    detalle = "\n".join(detalle_lineas)
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
