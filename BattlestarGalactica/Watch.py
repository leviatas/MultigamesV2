#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Modo espectador (/watch): reenvía por privado una copia de cada mensaje
que el bot envía al chat de una partida de BSG, a los uids en
`game.board.state.watchers`.

Se implementa reasignando la clase del bot a una subclase de `ExtBot` que
sobreescribe `send_message`/`send_photo` (ver `activar_relay`, llamado desde
MainController al construir la Application), en vez de instrumentar cada
punto de envío dentro de Controller.py/Commands.py — así cubre cualquier
acción futura sin tocar el resto del módulo.

No se puede lograr esto asignando `bot.send_message = ...` como atributo de
instancia: `telegram.ext.ExtBot` define `__slots__`, así que ese tipo de
parche crashea con `AttributeError` al arrancar el bot.
"""
import logging as log

from telegram.constants import ParseMode
from telegram.ext import ExtBot

import GamesController

logger = log.getLogger(__name__)


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


class _WatchRelayExtBot(ExtBot):
    """Subclase de ExtBot que espeja send_message/send_photo a los
    espectadores de BSG. No agrega slots propios para poder reasignarse
    como clase de una instancia de ExtBot ya construida (ver activar_relay)."""

    __slots__ = ()

    async def send_message(self, chat_id, text="", *args, **kwargs):
        result = await super().send_message(chat_id, text, *args, **kwargs)
        game = _juego_bsg_con_watchers(chat_id)
        if game:
            await _relay_text(self, game, text)
        return result

    async def send_photo(self, chat_id, photo, *args, caption=None, **kwargs):
        result = await super().send_photo(chat_id, photo, *args, caption=caption, **kwargs)
        game = _juego_bsg_con_watchers(chat_id)
        if game:
            # No se reenvía la imagen (el stream ya fue consumido); se informa
            # el texto/caption como aviso de que hubo un envío gráfico.
            await _relay_text(self, game, f"📷 {caption}" if caption else "📷 (imagen del tablero)")
        return result


def activar_relay(bot):
    """Convierte `bot` en un espejo para los espectadores de BSG,
    reasignando su clase a `_WatchRelayExtBot`. Idempotente: llamar más de
    una vez no vuelve a aplicar el cambio."""
    if isinstance(bot, _WatchRelayExtBot):
        return
    bot.__class__ = _WatchRelayExtBot
