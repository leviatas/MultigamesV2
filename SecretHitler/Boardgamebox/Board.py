from SecretHitler.Constants.Cards import playerSets
from SecretHitler.Constants.Cards import socialistSets
from SecretHitler.Constants.Cards import policies
from SecretHitler.Constants.Cards import CENSURA_DESDE
import random
from SecretHitler.Boardgamebox.State import State

class Board(object):
    def __init__(self, playercount, game):
        self.state = State()
        self.num_players = playercount
        self.modo = getattr(game, "modo", "clasico")
        if self.modo == "socialista":
            cartas = socialistSets[self.num_players]
            self.socialist_track_actions = cartas["socialist_track"]
            self.liberal_track_size = cartas["liberal_track"]
        else:
            cartas = playerSets[self.num_players]
            self.socialist_track_actions = []
            self.liberal_track_size = 5
        self.fascist_track_actions = cartas["track"]
        self.policies = random.sample(cartas["policies"], len(cartas["policies"]))
        self.discards = []
        self.previous = []

    def es_socialista(self):
        return getattr(self, "modo", "clasico") == "socialista"

    def socialist_track_size(self):
        # Cuantas politicas socialistas hacen falta para que ganen los socialistas.
        return len(getattr(self, "socialist_track_actions", []))

    def hay_censura(self):
        # La Censura no es el poder de una casilla: se activa al llegar a CENSURA_DESDE
        # politicas socialistas y queda activa el resto de la partida, igual que la Zona Hitler.
        return self.es_socialista() and self.state.socialist_track >= CENSURA_DESDE

    def print_board(self, player_sequence):
        liberal_track_size = getattr(self, "liberal_track_size", 5)
        board = "--- Actas Liberales ---\n"
        for i in range(liberal_track_size):
            if i < self.state.liberal_track:
                board += u"\u2716\uFE0F" + " " #X
            elif i >= self.state.liberal_track and i == liberal_track_size - 1:
                board += u"\U0001F54A" + " " #dove
            else:
                board += u"\u25FB\uFE0F" + " " #empty
        board += "\n--- Actas Fascistas ---\n"
        for i in range(6):
            if i < self.state.fascist_track:
                board += u"\u2716\uFE0F" + " " #X
            else:
                action = self.fascist_track_actions[i]
                if action == None:
                    board += u"\u25FB\uFE0F" + " "  # empty
                elif action == "policy":
                    board += u"\U0001F52E" + " " # crystal
                elif action == "inspect":
                    board += u"\U0001F50E" + " " # inspection glass
                elif action == "kill":
                    board += u"\U0001F5E1" + " " # knife
                elif action == "win":
                    board += u"\u2620" + " " # skull
                elif action == "choose":
                    board += u"\U0001F454" + " " # tie

        if self.es_socialista():
            board += "\n--- Actas Socialistas ---\n"
            for i in range(self.socialist_track_size()):
                if i < self.state.socialist_track:
                    board += u"\u2716\uFE0F" + " " #X
                else:
                    action = self.socialist_track_actions[i]
                    if action == "escucha":
                        board += u"\U0001F41B" + " " # bug
                    elif action == "reclutamiento":
                        board += u"\u270A" + " " # raised fist
                    elif action == "plan_quinquenal":
                        board += u"\u0035\uFE0F\u20E3" + " " # keycap 5
                    elif action == "congreso":
                        board += u"\U0001F3DB" + " " # classical building
                    elif action == "confesion":
                        board += u"\U0001F4D6" + " " # open book
                    elif action == "win":
                        board += u"\u262D" + " " # hammer and sickle
                    else:
                        board += u"\u25FB\uFE0F" + " "  # empty

        board += "\n--- Contador de elección ---\n"
        for i in range(3):
            if i < self.state.failed_votes:
                board += u"\u2716\uFE0F" + " " #X
            else:
                board += u"\u25FB\uFE0F" + " " #empty

        board += "\n--- Orden Presidencial  ---\n"
        for player in player_sequence:
            nombre = player.name.replace("_", " ")
            if self.state.nominated_president == player:
                board += "*" + nombre + "*" + " " + u"\u27A1\uFE0F" + " "
            else:
                board += nombre + " " + u"\u27A1\uFE0F" + " "
        board = board[:-3]
        board += u"\U0001F501"
        board += "\n\nHay " + str(len(self.policies)) + " politicas restantes en el mazo de politicas."
        if self.state.fascist_track >= 3:
            board += "\n\n" + u"\u203C\uFE0F" + " Cuidado: Si Hitler es elegido como Canciller los fascistas ganan el juego! " + u"\u203C\uFE0F"
        if self.hay_censura():
            board += "\n\n" + u"\U0001F576" + " Censura activa: ya no se elige Presidente de la Cámara."
        if len(self.state.not_hitlers) > 0:
            board += "\n\nSabemos que los siguientes jugadores no son Hitler porque fueron elegidos Canciller despues de 3 politicas fascistas:\n"
            for nh in self.state.not_hitlers:
                board += nh.name + ", "
            board = board[:-2]
        return board
