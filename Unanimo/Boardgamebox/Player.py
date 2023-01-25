from Boardgamebox.Player import Player as BasePlayer

class Player(BasePlayer):
    def __init__(self, name, uid):
        BasePlayer.__init__(self, name, uid)
        self.rol = None
        self.afiliacion = None
        self.is_mayor = False
        self.dople_rol = None
        self.dople_afiliacion = None
        self.points = 0

    def get_private_info(self, game):
        board = "--- Info del Jugador {} en la partida *{}*---\n".format(self.name, game.groupName)
        if game.board:
            board += "Tu rol es: *{}* con afiliacion *{}*".format(self.rol, self.afiliacion)
            if self.is_werewolf() or self.is_vidente() or self.is_mayor or (self.is_aprendiz and game.board.state.aprendiz_vidente):
                board += "\nTe recuerdo que la palabra magica es: *{}*".format(game.board.magic_word)
            board += "\n*ERES EL MAYOR*" if self.is_mayor else ""

        return board