from Boardgamebox.State import State as BaseState


class State(BaseState):
    def __init__(self):
        BaseState.__init__(self)
        # Fases: "Pujando" -> "Finalizado"
        self.fase_actual = "Pujando"
        self.ronda = 1
        # Pozo de la ronda actual (bananas del jugador que va ganando)
        self.pozo_actual = 0
        # Pujas secretas de la ronda actual {uid: cantidad}
        self.last_votes = {}
        self.ganador_uid = None
