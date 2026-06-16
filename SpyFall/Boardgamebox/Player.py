from Boardgamebox.Player import Player as BasePlayer


class Player(BasePlayer):
    def __init__(self, name, uid):
        BasePlayer.__init__(self, name, uid)
        self.role = None
        self.is_spy = False
