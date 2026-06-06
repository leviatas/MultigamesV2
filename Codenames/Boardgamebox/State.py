from Boardgamebox.State import State as BaseState


class State(BaseState):
    def __init__(self):
        BaseState.__init__(self)

        # list[dict]: {"word": str, "tipo": str, "revealed": bool, "numero": int}
        self.tablero = []

        self.spymaster_rojo = None
        self.spymaster_azul = None

        self.turno_actual = None          # "Rojo" | "Azul"
        self.pista_actual = None          # str
        self.numero_pista = 0
        self.intentos_restantes = 0

        self.palabras_rojo_restantes = 9
        self.palabras_azul_restantes = 8

        self.equipo_rojo = []             # list[Player]
        self.equipo_azul = []             # list[Player]
