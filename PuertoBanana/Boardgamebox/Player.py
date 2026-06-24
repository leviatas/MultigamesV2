from Boardgamebox.Player import Player as BasePlayer

BANANAS_INICIALES = 10


class Player(BasePlayer):
    def __init__(self, name, uid):
        BasePlayer.__init__(self, name, uid)
        self.bananas = BANANAS_INICIALES
        self.eliminado_ronda = False

    def get_private_info(self, game):
        return f"--- 🍌 Info de {self.name} ---\nTenés *{self.bananas}* bananas."
