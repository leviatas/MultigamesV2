from Boardgamebox.State import State as BaseState


class State(BaseState):
    def __init__(self):
        BaseState.__init__(self)
        self.localidad = None
        self.spy_uid = None
        self.fase_actual = "Interrogando"
        self.votos_acusacion = {}
        self.acusador_uid = None
        self.acusado_uid = None
        self.voto_msg_id = None
