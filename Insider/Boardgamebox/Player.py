from Boardgamebox.Player import Player as BasePlayer


class Player(BasePlayer):
    def __init__(self, name, uid):
        BasePlayer.__init__(self, name, uid)
        self.role = None        # "Guía" | "Infiltrado" | "Ciudadano"
        self.is_guia = False
        self.is_insider = False
