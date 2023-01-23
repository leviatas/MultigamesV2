from Boardgamebox.Player import Player as BasePlayer
import random

class Player(BasePlayer):
    def __init__(self, name, uid):
        BasePlayer.__init__(self, name, uid)
        self.rol = None
        self.afiliacion = None        
        self.means = []
        self.clues = []
        self.clue = None
        self.mean = None
        self.bullet_marker = 6
        self.accused = False
        self.accused_player = None
        self.accused_clue = None
        self.accused_mean = None

    def get_str_means_clues(self):
        clues_str = ", ".join(self.clues)
        clues_str[:-2]
        means_str = ", ".join(self.means)
        means_str[:-2]
        return "Medios: *{}*\nPistas: _{}_.".format(means_str, clues_str)

    def get_private_info(self, game):
        board = "--- Info del Jugador {} en la partida *{}*---\n".format(self.name, game.groupName)
        if game.board:
            board += "Tu rol es: *{}* con afiliacion *{}*\n".format(self.rol, self.afiliacion)
            board += self.get_str_means_clues()
            if self.is_testigo():
                asesino = game.get_asesino()
                complice = game.get_complice()
                zar  = random.randint(1,2)
                if zar == 1:
                    board += "Los sospechosos son: *{}* *{}*".format(asesino.name, complice.name)
                else:
                    board += "Los sospechosos son: *{}* *{}*".format(complice.name, asesino.name)
            if self.is_complice():
                asesino = game.get_asesino()
                board += "El asesino es *{}*. Pista *{}* Medio *{}*\n".format(asesino.name, asesino.clue, asesino.mean)
            if self.is_asesino():
                complice = game.get_complice()
                board += "*Sos el asesino*: Pista *{}* Medio *{}*\n".format(self.clue, self.mean)
                board += "*Tu complice es *{}*\n".format(complice.name)
            if self.is_forense():
                asesino = game.get_asesino()
                complice = game.get_complice()
                testigo = game.get_testigo()
                board += "El asesino es *{}*. Pista *{}* Medio *{}*\n".format(asesino.name, asesino.clue, asesino.mean)
                board += "El complice es *{}* y el complice es {}\n".format(complice.name, testigo.clue)         
        return board

    def is_accusation_true(self, accused_clue, accused_mean):
        return self.is_asesino() and self.clue == accused_clue and self.mean == accused_mean
    def is_role(self, role_name):
        return self.rol == role_name    
    def is_forense(self):
        return self.is_role("Forense")

    def is_asesino(self):
        return self.is_role("Asesino")
    
    def is_complice(self):
        return self.is_role("Complice")

    def is_testigo(self):
        return self.is_role("Testigo")

    def is_investigador(self):
        return self.is_role("Investigador")
