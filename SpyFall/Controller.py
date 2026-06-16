#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging as log
import random

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode

from Utils import get_game, save
from Constants.Config import ADMIN
from SpyFall.Constants.Locations import LOCALIDADES, LISTA_LOCALIDADES

import GamesController

log.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=log.INFO)
logger = log.getLogger(__name__)


def init_game(bot, game):
    try:
        log.info("SpyFall init_game called")
        game.shuffle_player_sequence()

        localidad = random.choice(LISTA_LOCALIDADES)
        roles = LOCALIDADES[localidad].copy()
        random.shuffle(roles)

        spy_uid = random.choice(list(game.playerlist.keys()))
        game.board.state.spy_uid = spy_uid
        game.board.state.localidad = localidad
        game.board.state.fase_actual = "Interrogando"

        role_index = 0
        for uid, player in game.playerlist.items():
            if uid == spy_uid:
                player.role = "Espía"
                player.is_spy = True
            else:
                player.role = roles[role_index % len(roles)]
                player.is_spy = False
                role_index += 1

        # Send DMs with roles
        bot.send_message(
            spy_uid,
            "🕵️ *¡Eres el ESPÍA!*\n\nNo conoces la localidad. Intenta descubrirla.\n\n"
            "Usa `/adivinar` en el grupo para adivinar la localidad en cualquier momento.",
            parse_mode=ParseMode.MARKDOWN
        )

        localidades_list = "\n".join(f"• {loc}" for loc in LISTA_LOCALIDADES)
        bot.send_message(
            spy_uid,
            f"📋 *Localidades posibles:*\n{localidades_list}",
            parse_mode=ParseMode.MARKDOWN
        )

        for uid, player in game.playerlist.items():
            if uid != spy_uid:
                bot.send_message(
                    uid,
                    f"🗺️ *Localidad: {localidad}*\n\n"
                    f"👤 *Tu rol: {player.role}*\n\n"
                    f"Haz preguntas para descubrir al espía sin revelar la localidad.",
                    parse_mode=ParseMode.MARKDOWN
                )

        player_names = "\n".join(f"• {p.name}" for p in game.player_sequence)
        bot.send_message(
            game.cid,
            f"🎮 *¡SpyFall ha comenzado!*\n\n"
            f"*Jugadores ({len(game.playerlist)}):*\n{player_names}\n\n"
            f"🕵️ Uno de ustedes es el *Espía*. ¡Descúbranlo!\n\n"
            f"📋 Revisen sus mensajes privados para conocer su rol.\n\n"
            f"*Comandos disponibles:*\n"
            f"• `/acusar` — Iniciar votación para identificar al espía\n"
            f"• `/adivinar` — (Solo espía) Adivinar la localidad\n"
            f"• `/rol` — Ver tu rol en privado",
            parse_mode=ParseMode.MARKDOWN
        )

        save(bot, game.cid)
    except Exception as e:
        logger.error(f"SpyFall init_game error: {e}")
        bot.send_message(ADMIN[0], f"SpyFall init_game error: {e}")
        raise


def resolve_accusation(bot, game):
    """Tally votes and determine if the spy was caught."""
    votes = game.board.state.votos_acusacion
    if not votes:
        bot.send_message(game.cid, "No hubo votos.", parse_mode=ParseMode.MARKDOWN)
        game.board.state.fase_actual = "Interrogando"
        save(bot, game.cid)
        return

    # Count how many votes each player received
    tally = {}
    for voter_uid, accused_uid in votes.items():
        tally[accused_uid] = tally.get(accused_uid, 0) + 1

    most_accused_uid = max(tally, key=lambda uid: tally[uid])
    most_accused_player = game.playerlist.get(most_accused_uid)
    vote_count = tally[most_accused_uid]

    tally_text = "\n".join(
        f"• {game.playerlist[uid].name}: {count} voto(s)"
        for uid, count in sorted(tally.items(), key=lambda x: -x[1])
        if uid in game.playerlist
    )

    bot.send_message(
        game.cid,
        f"📊 *Resultados de la votación:*\n{tally_text}\n\n"
        f"El más acusado: *{most_accused_player.name}* con {vote_count} voto(s)",
        parse_mode=ParseMode.MARKDOWN
    )

    if most_accused_player.is_spy:
        non_spy_wins(bot, game, caught=True)
    else:
        spy_wins(bot, game, reason=f"¡*{most_accused_player.name}* es inocente!")


def spy_wins(bot, game, reason=""):
    """Announce spy victory and end the game."""
    spy_player = game.playerlist.get(game.board.state.spy_uid)
    localidad = game.board.state.localidad

    game.board.state.fase_actual = "Finalizado"
    save(bot, game.cid)

    prefix = f"{reason}\n\n" if reason else ""
    bot.send_message(
        game.cid,
        f"{prefix}🕵️ *¡El espía gana!*\n\n"
        f"El espía era: *{spy_player.name}*\n"
        f"La localidad secreta era: *{localidad}*",
        parse_mode=ParseMode.MARKDOWN
    )


def non_spy_wins(bot, game, caught=False, guessed_wrong=False):
    """Announce non-spy victory and end the game."""
    spy_player = game.playerlist.get(game.board.state.spy_uid)
    localidad = game.board.state.localidad

    game.board.state.fase_actual = "Finalizado"
    save(bot, game.cid)

    if caught:
        msg = (
            f"✅ *¡El espía fue descubierto!*\n\n"
            f"El espía era: *{spy_player.name}*\n"
            f"La localidad secreta era: *{localidad}*\n\n"
            f"🏆 *¡Los no-espías ganan!*"
        )
    else:
        msg = (
            f"❌ *El espía no pudo adivinar la localidad.*\n\n"
            f"El espía era: *{spy_player.name}*\n"
            f"La localidad secreta era: *{localidad}*\n\n"
            f"🏆 *¡Los no-espías ganan!*"
        )

    bot.send_message(game.cid, msg, parse_mode=ParseMode.MARKDOWN)
