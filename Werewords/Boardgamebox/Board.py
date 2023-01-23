# Base Board
from Boardgamebox.Board import Board as BaseBoard
from Werewords.Boardgamebox.State import State

import random
from Werewords.Boardgamebox.State import State
from telegram import ParseMode

class Board(BaseBoard):
    def __init__(self, playercount, game):
        self.state = State()
        self.num_players = playercount
        self.cards = []
        self.discards = []
        self.magic_word = None
        
    def print_board(self, bot, game):
        board = "*Estado de partida:*\nPreguntas restantes:{}\n\nJugadores:\n".format(self.state.preguntas_restantes)
        for player in game.player_sequence:
            if self.state.mayor == player:
                board += "*" + player.name + " (Mayor)*" + " " + u"\u27A1\uFE0F" + " "
            else:
                board += player.name + " " + u"\u27A1\uFE0F" + " "
        board = board[:-1]
        board += u"\U0001F501"

        board += "\n\n"
        bot.send_message(game.cid, board, parse_mode=ParseMode.MARKDOWN)
        puede_hablar = " NO" if game.board.state.fase_actual == "preguntar" else ""
        bot.send_message(game.cid, "*Mayor {}{} puedes hablar*".format(game.board.state.mayor.name, puede_hablar), parse_mode=ParseMode.MARKDOWN)