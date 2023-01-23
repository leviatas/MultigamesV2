from Boardgamebox.Player import Player as BasePlayer

class Player(BasePlayer):
    def __init__(self, name, uid):
        BasePlayer.__init__(self, name, uid)
        self.rol = None
        self.afiliacion = None
        self.is_mayor = False
        self.dople_rol = None
        self.dople_afiliacion = None

    def get_private_info(self, game):
        board = "--- Info del Jugador {} en la partida *{}*---\n".format(self.name, game.groupName)
        if game.board:
            board += "Tu rol es: *{}* con afiliacion *{}*".format(self.rol, self.afiliacion)
            if self.is_werewolf() or self.is_vidente() or self.is_mayor or (self.is_aprendiz and game.board.state.aprendiz_vidente):
                board += "\nTe recuerdo que la palabra magica es: *{}*".format(game.board.magic_word)
            board += "\n*ERES EL MAYOR*" if self.is_mayor else ""

        return board

    
    def is_aprendiz(self):
        return self.rol == "Aprendiz" or self.dople_rol == "Aprendiz"

    def is_vidente(self):
        return self.rol == "Vidente" or self.dople_rol == "Vidente"
    
    def is_werewolf_team(self):
        return self.afiliacion == "Hombre Lobo" or self.dople_afiliacion == "Hombre Lobo"

    def is_werewolf(self):
        return self.rol == "Hombre Lobo" or self.dople_rol == "Hombre Lobo"

    def is_minion(self):
        return self.rol == "Secuaz" or self.dople_rol == "Secuaz"
