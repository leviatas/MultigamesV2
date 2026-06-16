#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging as log
import os
import random
import re

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

from Utils import get_game, save, simple_choose_buttons, player_call
from Constants.Config import ADMIN
from Insider.Boardgamebox.Game import Game

import GamesController

_TXT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'txt')

log.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=log.INFO)
logger = log.getLogger(__name__)


async def init_game(bot, game):
    try:
        log.info("Insider init_game called")
        game.shuffle_player_sequence()
        st = game.board.state

        uids = list(game.playerlist.keys())
        guia_uid = random.choice(uids)
        restantes = [u for u in uids if u != guia_uid]
        infiltrado_uid = random.choice(restantes)

        st.guia_uid = guia_uid
        st.infiltrado_uid = infiltrado_uid
        st.fase_actual = "Preguntas"

        # Palabra secreta
        url_palabras = os.path.join(_TXT_DIR, 'spanish-original.txt')
        with open(url_palabras, 'r') as f:
            palabras = [w.strip() for w in f if w.strip()]
        palabra = random.choice(palabras)
        st.palabra = palabra

        for uid, player in game.playerlist.items():
            if uid == guia_uid:
                player.role = "Guía"
                player.is_guia = True
                player.is_insider = False
            elif uid == infiltrado_uid:
                player.role = "Infiltrado"
                player.is_guia = False
                player.is_insider = True
            else:
                player.role = "Ciudadano"
                player.is_guia = False
                player.is_insider = False

        # DMs con los roles
        await bot.send_message(
            guia_uid,
            f"👑 *Eres el GUÍA.*\n\nLa palabra secreta es: *{palabra}*\n\n"
            "Responde solo *sí*, *no* o *no lo sé* a las preguntas de los demás.\n\n"
            "Cuando alguien adivine la palabra, usa `/acerto` en el grupo para marcar quién fue.\n"
            "Si se acaba el tiempo y nadie acierta, usa `/notiempo`.",
            parse_mode=ParseMode.MARKDOWN
        )
        await bot.send_message(
            infiltrado_uid,
            f"🕵️ *Eres el INFILTRADO.*\n\nLa palabra secreta es: *{palabra}*\n\n"
            "Guía disimuladamente a los demás hacia la palabra... ¡pero que no te descubran!",
            parse_mode=ParseMode.MARKDOWN
        )
        for uid, player in game.playerlist.items():
            if uid not in (guia_uid, infiltrado_uid):
                await bot.send_message(
                    uid,
                    "👥 *Eres un CIUDADANO.*\n\nNo conoces la palabra secreta. "
                    "Haz preguntas de sí/no al Guía para adivinarla... y desconfía: "
                    "uno de ustedes es el Infiltrado.",
                    parse_mode=ParseMode.MARKDOWN
                )

        guia_name = game.playerlist[guia_uid].name
        player_names = "\n".join(f"• {p.name}" for p in game.player_sequence)
        await bot.send_message(
            game.cid,
            f"🎭 *¡Insider ha comenzado!*\n\n"
            f"*Jugadores ({len(game.playerlist)}):*\n{player_names}\n\n"
            f"👑 El *Guía* es: *{guia_name}* (eligió una palabra secreta).\n"
            f"Entre los demás se esconde un *Infiltrado* que también la conoce.\n\n"
            f"⏳ *Fase de Preguntas:* hagan preguntas de sí/no al Guía para adivinar la palabra "
            f"antes de que se acabe el tiempo acordado (sugerido: 5 minutos).\n\n"
            f"*Comandos:*\n"
            f"• `/acerto` — (Guía) marcar quién adivinó la palabra\n"
            f"• `/notiempo` — (Guía) se acabó el tiempo, nadie acertó\n"
            f"• `/mirol` — ver tu rol en privado",
            parse_mode=ParseMode.MARKDOWN
        )

        await save(bot, game.cid)
    except Exception as e:
        logger.error(f"Insider init_game error: {e}")
        await bot.send_message(ADMIN[0], f"Insider init_game error: {e}")
        raise


# --- Fase Juzgar (¿el que acertó es el infiltrado?) ---

async def start_juzgar(bot, game):
    st = game.board.state
    st.fase_actual = "Juzgar"
    st.votos_juzgar = {}
    acertador = game.playerlist[st.acertador_uid]

    btns = [
        [InlineKeyboardButton("🙋 Sí, es el Infiltrado", callback_data=f"{game.cid}*insiderJuzgar*si*0")],
        [InlineKeyboardButton("🙅 No lo es", callback_data=f"{game.cid}*insiderJuzgar*no*0")],
    ]
    await bot.send_message(
        game.cid,
        f"✅ *{acertador.name}* adivinó la palabra: *{st.palabra}*\n\n"
        f"💬 *Discutan:* ¿la pregunta final fue sospechosa? ¿{acertador.name} es el Infiltrado?\n\n"
        f"🗳️ Cuando estén listos, *voten*: ¿creen que *{acertador.name}* es el Infiltrado?\n"
        f"(Votan todos menos {acertador.name}.)",
        reply_markup=InlineKeyboardMarkup(btns),
        parse_mode=ParseMode.MARKDOWN
    )
    await save(bot, game.cid)


async def resolve_juzgar(bot, game):
    st = game.board.state
    total = len(game.playerlist)
    si = sum(1 for v in st.votos_juzgar.values() if v)
    # Mayoría: más de la mitad del total de jugadores (con 6 → se necesitan 4)
    mayoria = si * 2 > total
    acertador = game.playerlist[st.acertador_uid]
    es_infiltrado = (st.acertador_uid == st.infiltrado_uid)

    await bot.send_message(
        game.cid,
        f"📊 Manos levantadas acusando a *{acertador.name}*: {si}/{total} "
        f"→ {'hay mayoría' if mayoria else 'no hay mayoría'}.",
        parse_mode=ParseMode.MARKDOWN
    )

    if mayoria:
        if es_infiltrado:
            await finish_game(
                bot, game, ciudadanos_ganan=True,
                detalle=f"🔎 *{acertador.name}* revela su rol: ¡era el *Infiltrado*!"
            )
        else:
            await finish_game(
                bot, game, ciudadanos_ganan=False,
                detalle=f"🔎 *{acertador.name}* revela su rol: era un *Ciudadano* inocente."
            )
    else:
        await start_votar(bot, game)


# --- Fase Votar (señalar al infiltrado) ---

async def start_votar(bot, game):
    st = game.board.state
    st.fase_actual = "Votar"
    st.votos_infiltrado = {}

    btns = []
    for p_uid, player in game.playerlist.items():
        if p_uid == st.guia_uid:
            continue  # el Guía conoce al Infiltrado: no es candidato ni vota
        btns.append([InlineKeyboardButton(player.name, callback_data=f"{game.cid}*insiderVotar*{p_uid}*0")])

    await bot.send_message(
        game.cid,
        "🗳️ *Votación final.* No hubo mayoría, así que cada jugador (excepto el Guía) "
        "señala a quién cree que es el *Infiltrado*:",
        reply_markup=InlineKeyboardMarkup(btns),
        parse_mode=ParseMode.MARKDOWN
    )
    await save(bot, game.cid)


async def resolve_votar(bot, game):
    st = game.board.state
    votos = st.votos_infiltrado
    if not votos:
        await finish_game(bot, game, ciudadanos_ganan=False, detalle="Nadie emitió su voto.")
        return

    tally = {}
    for accused in votos.values():
        tally[accused] = tally.get(accused, 0) + 1

    tally_text = "\n".join(
        f"• {game.playerlist[u].name}: {c} voto(s)"
        for u, c in sorted(tally.items(), key=lambda x: -x[1])
        if u in game.playerlist
    )
    await bot.send_message(game.cid, f"📊 *Votación final:*\n{tally_text}", parse_mode=ParseMode.MARKDOWN)

    maxv = max(tally.values())
    top = [u for u, c in tally.items() if c == maxv]
    if len(top) > 1:
        await pedir_desempate(bot, game, top)
        return
    await resolver_acusado(bot, game, top[0])


async def pedir_desempate(bot, game, candidatos):
    st = game.board.state
    st.fase_actual = "Desempate"
    st.empate_candidatos = candidatos
    acertador = game.playerlist[st.acertador_uid]

    btns = [
        [InlineKeyboardButton(
            game.playerlist[u].name,
            callback_data=f"{game.cid}*insiderDesempate*{u}*{st.acertador_uid}"
        )]
        for u in candidatos
    ]
    await bot.send_message(
        game.cid,
        f"🤝 *¡Empate!* {player_call(acertador)} (quien adivinó la palabra) debe decidir "
        f"quién tiene la mayoría:",
        reply_markup=InlineKeyboardMarkup(btns),
        parse_mode=ParseMode.MARKDOWN
    )
    await save(bot, game.cid)


async def resolver_acusado(bot, game, accused_uid):
    st = game.board.state
    acusado = game.playerlist.get(accused_uid)
    if accused_uid == st.infiltrado_uid:
        await finish_game(
            bot, game, ciudadanos_ganan=True,
            detalle=f"🔎 *{acusado.name}* era el *Infiltrado*. ¡Lo descubrieron!"
        )
    else:
        await finish_game(
            bot, game, ciudadanos_ganan=False,
            detalle=f"🔎 *{acusado.name}* era inocente. El Infiltrado logró escapar."
        )


# --- Fin de partida ---

async def todos_pierden(bot, game):
    st = game.board.state
    await finish_game(
        bot, game, ciudadanos_ganan=False,
        detalle="⌛ Se acabó el tiempo y nadie adivinó la palabra. *¡Todos pierden!*",
        gana_infiltrado=False
    )


async def finish_game(bot, game, ciudadanos_ganan, detalle="", gana_infiltrado=True):
    st = game.board.state
    st.fase_actual = "Finalizado"
    await save(bot, game.cid)

    guia = game.playerlist.get(st.guia_uid)
    infiltrado = game.playerlist.get(st.infiltrado_uid)

    if ciudadanos_ganan:
        resultado = "🏆 *¡Ganan el Guía y los Ciudadanos!*"
    elif gana_infiltrado:
        resultado = "🕵️ *¡Gana el Infiltrado!*"
    else:
        resultado = "💀 *Nadie gana.*"

    await bot.send_message(
        game.cid,
        f"{detalle}\n\n{resultado}\n\n"
        f"La palabra secreta era: *{st.palabra}*\n"
        f"👑 Guía: *{guia.name}*\n"
        f"🕵️ Infiltrado: *{infiltrado.name}*",
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
        "chooseendInsider",
        "¿Quieres continuar jugando?",
        opciones_botones,
    )


async def callback_finish_game_buttons_insider(update: Update, context: CallbackContext):
    bot = context.bot
    callback = update.callback_query
    try:
        regex = re.search(r"(-[0-9]*)\*chooseendInsider\*(.*)\*([0-9]*)", callback.data)
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

        new_game.playerlist = players
        new_game.board = None
        new_game.create_board()
        new_game.player_sequence = []
        await init_game(bot, new_game)
    except Exception as e:
        await bot.send_message(ADMIN[0], f'callback_finish_game_buttons_insider error: {e}')
        await bot.send_message(ADMIN[0], callback.data)
