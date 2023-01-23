import json
from datetime import datetime
from random import shuffle

from Boardgamebox.Player import Player
from Boardgamebox.State import State

from Utils import get_config_data

class Game(object):
    def __init__(self, cid, initiator, groupName, tipo = None, modo = None, ):
        self.playerlist = {}
        self.player_sequence = []
        self.cid = cid
        self.board = None
        self.initiator = initiator
        self.dateinitvote = None
        self.history = []
        self.hiddenhistory = []
        # Nombre del juego que se jugará LostExpedition, JustOne...
        self.tipo = tipo
        # Modo de juego solitario, coopertativo, competitivo...
        self.modo = modo
        # Nombre del grupo cuando se creo...
        self.groupName  = groupName
        # Configuraciones variadas...
        self.configs = {}
        # Modo para debugear a futuras partidas
        self.is_debugging = False
    
    def getPlayerTeam(self, uid):
        for team in self.board.state.teams:
            if (team.belongs(uid)):
                return team

    def getHistory(self, uid):
        history_list = []
        history_text = "History del grupo *{}*:\n\n".format(self.groupName) 
        for x in self.history:
            if len(history_text) < 3500:
                history_text += x + "\n\n"
            else:
                history_list.append(history_text)
                history_text = ""
        return history_list
    
    def add_player(self, uid, name):
        self.playerlist[uid] = Player(name, uid)    

    def find_player(self, name):
        for uid in self.playerlist:
            if self.playerlist[uid].name == name:
                return self.playerlist[uid]
        for player in self.player_sequence:
            if player.name == name:
                return player
        return None
    
    def shuffle_player_sequence(self):
        for uid in self.playerlist:
            self.player_sequence.append(self.playerlist[uid])
        shuffle(self.player_sequence)

    def remove_from_player_sequence(self, Player):
        for p in self.player_sequence:
            if p.uid == Player.uid:
                self.player_sequence.remove(p)
                return
    
    def increment_player_counter(self, game):
        if self.board.state.player_counter < len(self.player_sequence) - 1:
            self.board.state.player_counter += 1
        else:
            self.board.state.player_counter = 0

    def get_rules(self):
        return ["LINK_Juego", "No hay reglas agregadas todavias:"]

    def call(self, context):
        import JustOne.Commands as JustoneCommands
        if self.board is not None:
            JustoneCommands.command_call(context.bot, self)

    def group_link_name(self):
        link_info = get_config_data(self, "link")
        if link_info == None:
            group_link_name = "*{0}*".format(self.groupName)
        else:
            group_link_name = "[{0}]({1})".format(self.groupName, link_info)
        return group_link_name

    def player_leaving(self, player):
        if self.tipo == "JustOne":
            # Si el usuario no es el que adivina, ni el revisor, lo dejo ir.
            if self.board.state.active_player.uid != player.uid and self.board.state.reviewer_player.uid != player.uid:
                # Lo saco de la player list y el juego deberia fluir                
                if player.uid in self.playerlist:
                    del self.playerlist[player.uid]
                self.remove_from_player_sequence(player)
                return "El jugador {} ha huido del chat. Que algun jugador haga clue para continuar.".format(player.name)
        return None