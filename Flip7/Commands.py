#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging as log

from Utils import player_call

log.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=log.INFO)
logger = log.getLogger(__name__)


def _validar_partida(game):
    return game and game.tipo == "Flip7" and game.board


async def command_call(bot, game):
    """Recordatorio de quién tiene que actuar en este momento."""
    if not _validar_partida(game):
        return
    st = game.board.state
    if st.fase_actual != "Jugando":
        return

    if st.accion_pendiente:
        drawer = game.playerlist.get(st.accion_pendiente.get("drawer_uid"))
        if drawer:
            await bot.send_message(
                game.cid,
                "⏳ Esperando que {} elija el objetivo de su carta de acción.".format(player_call(drawer)),
                parse_mode="Markdown"
            )
        return

    if st.active_player is not None:
        await bot.send_message(
            game.cid,
            "⏳ Esperando que {} decida: pedir carta o plantarse.".format(player_call(st.active_player)),
            parse_mode="Markdown"
        )
