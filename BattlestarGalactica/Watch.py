#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Modo espectador (/watch): reenvía por privado una copia de cada mensaje
que el bot envía al chat de una partida de BSG, a los uids en
`game.board.state.watchers`.

Se implementa parcheando una única vez los métodos `send_message` y
`send_photo` del bot (ver `activar_relay`, llamado desde MainController al
construir la Application), en vez de instrumentar cada punto de envío
dentro de Controller.py/Commands.py — así cubre cualquier acción futura sin
tocar el resto del módulo.
"""
import logging as log

from telegram.constants import ParseMode

import GamesController

logger = log.getLogger(__name__)

_PATCHED_ATTR = "_bsg_watch_patched"


def _juego_bsg_con_watchers(chat_id):
    game = GamesController.games.get(chat_id)
    if not game or game.tipo != "BattlestarGalactica" or not game.board:
        return None
    watchers = getattr(game.board.state, "watchers", None)
    if not watchers:
        return None
    return game


async def _relay_text(bot, game, texto):
    if not texto:
        return
    cuerpo = f"👁 *[{game.groupName}]*\n{texto}"
    for w_uid in list(game.board.state.watchers):
        try:
            await bot.send_message(w_uid, cuerpo, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            logger.error(f"BSG watch relay error (uid {w_uid}): {e}")


def activar_relay(bot):
    """Parchea bot.send_message/send_photo para espejar a los espectadores.
    Idempotente: llamar más de una vez no duplica el parche."""
    if getattr(bot, _PATCHED_ATTR, False):
        return

    original_send_message = bot.send_message
    original_send_photo = bot.send_photo

    async def send_message_con_relay(chat_id, text="", *args, **kwargs):
        result = await original_send_message(chat_id, text, *args, **kwargs)
        game = _juego_bsg_con_watchers(chat_id)
        if game:
            await _relay_text(bot, game, text)
        return result

    async def send_photo_con_relay(chat_id, photo, *args, caption=None, **kwargs):
        result = await original_send_photo(chat_id, photo, *args, caption=caption, **kwargs)
        game = _juego_bsg_con_watchers(chat_id)
        if game:
            # No se reenvía la imagen (el stream ya fue consumido); se informa
            # el texto/caption como aviso de que hubo un envío gráfico.
            await _relay_text(bot, game, f"📷 {caption}" if caption else "📷 (imagen del tablero)")
        return result

    bot.send_message = send_message_con_relay
    bot.send_photo = send_photo_con_relay
    setattr(bot, _PATCHED_ATTR, True)
