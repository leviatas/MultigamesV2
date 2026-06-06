from Boardgamebox.Player import Player as BasePlayer


class Player(BasePlayer):
    def __init__(self, name, uid):
        BasePlayer.__init__(self, name, uid)
        self.equipo = None      # "Rojo" | "Azul"
        self.es_espia = False

    def get_private_info(self, game):
        board = f"--- Info de {self.name} ---\n"
        board += f"Equipo: {self.equipo}\n"
        board += f"Rol: {'Espía' if self.es_espia else 'Agente de Campo'}\n"
        if self.es_espia and game.board:
            board += "\n" + game.board.print_spymaster_board(game)
        return board
