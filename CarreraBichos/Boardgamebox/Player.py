from Boardgamebox.Player import Player as BasePlayer
from CarreraBichos.Constants.Cartas import carta_txt


class Player(BasePlayer):
    def __init__(self, name, uid):
        BasePlayer.__init__(self, name, uid)
        self.dinero = 0
        self.mano = []       # cartas en la mano (privadas)
        self.apuestas = []   # [{"t": clave_boleto, "pago": int, "fuerte": bool}]
        self.aporto = False

    def get_private_info(self, game):
        from CarreraBichos.Motor import boleto_txt
        texto = "--- 🏟️ *Carrera de Bichos* — {} ---\n".format(self.name)
        texto += "Dinero: *${}*\n\n".format(self.dinero)
        if self.apuestas:
            texto += "*Tus apuestas:*\n" + "\n".join(
                "• {}{} (paga ${})".format(boleto_txt(game, a["t"]), " 🔥" if a["fuerte"] else "", a["pago"])
                for a in self.apuestas) + "\n\n"
        texto += "*Tu mano:* " + (", ".join(carta_txt(c) for c in self.mano) or "-")
        return texto
