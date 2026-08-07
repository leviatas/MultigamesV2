#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Modo espectador (/watch): reenvía por privado una copia de cada mensaje
relacionado con una partida de BSG a los uids en `game.board.state.watchers`
— tanto los mensajes al chat del grupo como los mensajes privados que el bot
le manda a cada jugador (sus decisiones y los resultados que solo él ve).

Se implementa reasignando la clase del bot a una subclase de `ExtBot` que
sobreescribe `send_message`/`send_photo` (ver `activar_relay`, llamado desde
MainController al construir la Application), en vez de instrumentar cada
punto de envío dentro de Controller.py/Commands.py — así cubre cualquier
acción futura sin tocar el resto del módulo.

No se puede lograr esto asignando `bot.send_message = ...` como atributo de
instancia: `telegram.ext.ExtBot` define `__slots__`, así que ese tipo de
parche crashea con `AttributeError` al arrancar el bot.

Límite conocido: el reenvío de privados identifica al destinatario solo por
su uid (¿es jugador de ALGUNA partida BSG con espectadores?), porque el
parche no sabe qué módulo originó cada envío. Si ese jugador participa a la
vez en otra partida (de BSG u otro juego) que también le escribe por
privado, esos mensajes ajenos también se reenviarían a los espectadores
mientras /watch esté activo. Es un caso raro y /watch ya es una herramienta
de admin de confianza, así que se acepta el riesgo en vez de instrumentar
cada punto de envío del módulo para evitarlo.
"""
import logging as log

from telegram.constants import ParseMode
from telegram.ext import ExtBot

import GamesController

logger = log.getLogger(__name__)


def _contexto_watch(chat_id):
    """Si chat_id es el grupo de una partida BSG con espectadores activos,
    o el privado de uno de sus jugadores, devuelve (game, jugador). jugador
    es el Player dueño de ese privado, o None si chat_id es el grupo.
    Devuelve None si no hay nada que reenviar."""
    game = GamesController.games.get(chat_id)
    if game is not None:
        if (game.tipo == "BattlestarGalactica" and game.board
                and getattr(game.board.state, "watchers", None)):
            return game, None
        return None
    # No es el grupo de ninguna partida: puede ser el privado de un jugador
    # de una partida BSG con espectadores activos.
    for g in GamesController.games.values():
        if (getattr(g, "tipo", None) == "BattlestarGalactica" and g.board
                and getattr(g.board.state, "watchers", None)):
            jugador = g.playerlist.get(chat_id)
            if jugador:
                return g, jugador
    return None


async def _relay_text(bot, game, jugador, texto):
    if not texto:
        return
    origen = f"{jugador.name} (privado)" if jugador else "grupo"
    cuerpo = f"👁 *[{game.groupName}]* — {origen}:\n{texto}"
    for w_uid in list(game.board.state.watchers):
        try:
            # Se llama a la implementación original (ExtBot.send_message),
            # nunca a la del propio bot ya parcheado: si no, reenviarle la
            # copia a un espectador que también es jugador de la partida
            # dispararía el relay de nuevo sobre esa copia y así sin fin.
            await ExtBot.send_message(bot, w_uid, cuerpo, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            logger.error(f"BSG watch relay error (uid {w_uid}): {e}")


class _WatchRelayExtBot(ExtBot):
    """Subclase de ExtBot que espeja send_message/send_photo a los
    espectadores de BSG. No agrega slots propios para poder reasignarse
    como clase de una instancia de ExtBot ya construida (ver activar_relay)."""

    __slots__ = ()

    async def send_message(self, chat_id, text="", *args, **kwargs):
        result = await super().send_message(chat_id, text, *args, **kwargs)
        ctx = _contexto_watch(chat_id)
        if ctx:
            game, jugador = ctx
            await _relay_text(self, game, jugador, text)
        return result

    async def send_photo(self, chat_id, photo, *args, caption=None, **kwargs):
        result = await super().send_photo(chat_id, photo, *args, caption=caption, **kwargs)
        ctx = _contexto_watch(chat_id)
        if ctx:
            game, jugador = ctx
            # No se reenvía la imagen (el stream ya fue consumido); se informa
            # el texto/caption como aviso de que hubo un envío gráfico.
            await _relay_text(self, game, jugador, f"📷 {caption}" if caption else "📷 (imagen del tablero)")
        return result


def activar_relay(bot):
    """Convierte `bot` en un espejo para los espectadores de BSG,
    reasignando su clase a `_WatchRelayExtBot`. Idempotente: llamar más de
    una vez no vuelve a aplicar el cambio."""
    if isinstance(bot, _WatchRelayExtBot):
        return
    bot.__class__ = _WatchRelayExtBot
