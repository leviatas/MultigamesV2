from Boardgamebox.State import State as BaseState


class State(BaseState):
    def __init__(self):
        BaseState.__init__(self)
        # Fases: "Preguntas" -> "Juzgar" -> "Votar" -> "Finalizado"
        self.fase_actual = "Preguntas"
        self.palabra = None
        self.guia_uid = None
        self.infiltrado_uid = None
        self.acertador_uid = None          # quien adivinó la palabra
        # Fase Juzgar: ¿el acertador es el infiltrado? {voter_uid: True/False}
        self.votos_juzgar = {}
        # Fase Votar: a quién señalan como infiltrado {voter_uid: accused_uid}
        self.votos_infiltrado = {}
        self.empate_candidatos = []        # candidatos en caso de empate en Votar
