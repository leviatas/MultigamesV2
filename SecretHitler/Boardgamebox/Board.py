from SecretHitler.Constants.Cards import playerSets
from SecretHitler.Constants.Cards import socialistSets
from SecretHitler.Constants.Cards import policies
from SecretHitler.Constants.Cards import CENSURA_DESDE
import random
from SecretHitler.Boardgamebox.State import State
from SecretHitler.i18n import t

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

    def print_board(self, player_sequence, ctx=None):
        # ctx: el Game (o un cid/idioma) del que se toma el idioma en que se dibuja el tablero.
        liberal_track_size = getattr(self, "liberal_track_size", 5)
        board = t("board.liberal_track", ctx) + "\n"
        for i in range(liberal_track_size):
            if i < self.state.liberal_track:
                board += u"✖️" + " " #X
            elif i >= self.state.liberal_track and i == liberal_track_size - 1:
                board += u"\U0001F54A" + " " #dove
            else:
                board += u"◻️" + " " #empty
        board += "\n" + t("board.fascist_track", ctx) + "\n"
        for i in range(6):
            if i < self.state.fascist_track:
                board += u"✖️" + " " #X
            else:
                action = self.fascist_track_actions[i]
                if action == None:
                    board += u"◻️" + " "  # empty
                elif action == "policy":
                    board += u"\U0001F52E" + " " # crystal
                elif action == "inspect":
                    board += u"\U0001F50E" + " " # inspection glass
                elif action == "kill":
                    board += u"\U0001F5E1" + " " # knife
                elif action == "win":
                    board += u"☠" + " " # skull
                elif action == "choose":
                    board += u"\U0001F454" + " " # tie

        if self.es_socialista():
            board += "\n" + t("board.socialist_track", ctx) + "\n"
            for i in range(self.socialist_track_size()):
                if i < self.state.socialist_track:
                    board += u"✖️" + " " #X
                else:
                    action = self.socialist_track_actions[i]
                    if action == "escucha":
                        board += u"\U0001F41B" + " " # bug
                    elif action == "reclutamiento":
                        board += u"✊" + " " # raised fist
                    elif action == "plan_quinquenal":
                        board += u"5️⃣" + " " # keycap 5
                    elif action == "congreso":
                        board += u"\U0001F3DB" + " " # classical building
                    elif action == "confesion":
                        board += u"\U0001F4D6" + " " # open book
                    elif action == "win":
                        board += u"☭" + " " # hammer and sickle
                    else:
                        board += u"◻️" + " "  # empty

        board += "\n" + t("board.election_tracker", ctx) + "\n"
        for i in range(3):
            if i < self.state.failed_votes:
                board += u"✖️" + " " #X
            else:
                board += u"◻️" + " " #empty

        board += "\n" + t("board.president_order", ctx) + "\n"
        for player in player_sequence:
            nombre = player.name.replace("_", " ")
            if self.state.nominated_president == player:
                board += "*" + nombre + "*" + " " + u"➡️" + " "
            else:
                board += nombre + " " + u"➡️" + " "
        board = board[:-3]
        board += u"\U0001F501"
        board += "\n\n" + t("board.policies_left", ctx, cantidad=len(self.policies))
        if self.state.fascist_track >= 3:
            board += "\n\n" + t("board.hitler_zone_warning", ctx)
        if self.hay_censura():
            board += "\n\n" + t("board.censorship_active", ctx)
        if len(self.state.not_hitlers) > 0:
            board += "\n\n" + t("board.not_hitlers", ctx) + "\n"
            for nh in self.state.not_hitlers:
                board += nh.name + ", "
            board = board[:-2]
        return board
