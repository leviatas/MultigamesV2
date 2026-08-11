from Boardgamebox.State import State as BaseState


class State(BaseState):
    def __init__(self):
        BaseState.__init__(self)
        # Fases: "Jugando" -> "RondaFinalizada" -> "Jugando" (siguiente ronda) o "Finalizado"
        self.fase_actual = "Jugando"
        self.ronda = 1
        # uid del jugador que debe seguir robando cartas de forma obligada (por Flip Three)
        self.forzado_uid = None
        # cuantas cartas forzadas le quedan por robar al jugador forzado
        self.forzado_restantes = 0
        # cola de uids en espera de resolver un Flip Three pendiente
        self.cola_flip_three = []
        # accion de un jugador esperando que elija objetivo/destinatario: {"tipo": ..., "drawer_uid": ...}
        self.accion_pendiente = None
        self.ganadores_uids = []
