#!/usr/bin/env python
# -*- coding: utf-8 -*-

import CarreraBichos.Controller as CBController


async def command_call(bot, game):
    """Recordatorio de quién tiene que actuar; si la transmisión se cortó, la retoma."""
    if not game or game.tipo != "CarreraBichos" or not game.board:
        return
    if game.board.state.fase_actual == "Finalizado":
        return
    await CBController.recordar(bot, game)
