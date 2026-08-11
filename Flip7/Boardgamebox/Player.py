from Boardgamebox.Player import Player as BasePlayer
from Flip7.Constants.Cards import card_display


class Player(BasePlayer):
    def __init__(self, name, uid):
        BasePlayer.__init__(self, name, uid)
        self.puntaje_total = 0
        # Números únicos recolectados en la ronda actual
        self.numeros = []
        # Modificadores recolectados en la ronda actual (ej: ["+4", "X2"])
        self.modificadores = []
        self.tiene_segunda_oportunidad = False
        # jugando | plantado | congelado | reventado | flip7
        self.estado_ronda = "jugando"

    def puntaje_ronda(self):
        if self.estado_ronda == "reventado":
            return 0
        suma_numeros = sum(self.numeros)
        if "X2" in self.modificadores:
            suma_numeros *= 2
        suma_mods = sum(int(m) for m in self.modificadores if m != "X2")
        bonus = 15 if self.estado_ronda == "flip7" else 0
        return suma_numeros + suma_mods + bonus

    def reset_ronda(self):
        self.numeros = []
        self.modificadores = []
        self.tiene_segunda_oportunidad = False
        self.estado_ronda = "jugando"

    def get_private_info(self, game):
        board = "--- 🎴 Info de {} ---\n".format(self.name)
        board += "Puntaje total: *{}*\n".format(self.puntaje_total)
        cartas_txt = ", ".join(card_display(n) for n in sorted(self.numeros)) or "-"
        board += "Números esta ronda: {}\n".format(cartas_txt)
        if self.modificadores:
            board += "Modificadores: {}\n".format(", ".join(self.modificadores))
        board += "Segunda Oportunidad: {}\n".format("Sí" if self.tiene_segunda_oportunidad else "No")
        board += "Puntaje de la ronda si te plantás ahora: *{}*".format(self.puntaje_ronda())
        return board
