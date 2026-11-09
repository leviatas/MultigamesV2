#!/usr/bin/env python
# -*- coding: utf-8 -*-

import GranPremioArcano.Controller as GPController


async def command_call(bot, game):
    """Recordatorio de quién tiene que actuar (y reenvía los botones perdidos)."""
    if not game or game.tipo != "GranPremioArcano" or not game.board:
        return
    if game.board.state.fase_actual == "Finalizado":
        return
    await GPController.recordar(bot, game)
