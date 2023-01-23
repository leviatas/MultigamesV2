# Base Board
from Boardgamebox.Board import Board as BaseBoard
from Deception.Boardgamebox.State import State

import random
from Deception.Boardgamebox.State import State
from telegram import ParseMode

class Board(BaseBoard):
    def __init__(self, playercount, game):
        self.state = State()
        self.num_players = playercount
        self.cards = []
        self.discards = []
        self.magic_word = None

    def get_forensic_cards_description(self, forensic_list = True, check_has_bullet = True, only_scenes = False):
        lista = self.state.forensic_cards if forensic_list else self.state.new_scene_event_card
        msg_descrp_loca = ""	
        for idx, card in enumerate(lista):
            for nombre, valores in card.items():
                if not any(x for x in valores.values() if list(x.items())[0][1]) or not check_has_bullet:
                    if not only_scenes or idx not in [0, 1]:
                        msg_descrp_loca += "*{}*:\n{}\n".format(nombre, ', '.join( "*{}*".format(list(x.items())[0][0]) if list(x.items())[0][1] else "{}".format(list(x.items())[0][0]) for x in [x for x in valores.values()]))
        msg_descrp_loca = msg_descrp_loca[:-1]
        return msg_descrp_loca

    def print_board(self, bot, game):
        board = "*Estado de partida:*\n"        
        for player in game.player_sequence:            
            if self.state.forense == player:
                board += "*" + player.name + " (Forense)*\n"
            else:
                board +=  "*{}*:\n{}\n".format(player.name, player.get_str_means_clues())
        board = board[:-1]

        board += "\n\n"
        msg_descrp_loca = self.get_forensic_cards_description(True, False, False)
        if (msg_descrp_loca != ""):
            board += "{}\n\n".format(msg_descrp_loca)

        board += "*Forense {} NO puedes hablar*".format(self.state.forense.name)
        board += "\nPara nueva evidencia usa /newevidence" if self.state.forense.bullet_marker == 0 else ""
        bot.send_message(game.cid, board, parse_mode=ParseMode.MARKDOWN)
