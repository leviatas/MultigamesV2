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

        # --- Modo Cooperativo "Dúo" (2 jugadores, mismo equipo) ---
        self.jugador_a = None
        self.jugador_b = None
        self.key_a = {}                   # {numero: "agente"|"neutral"|"asesino"} — vista del jugador A
        self.key_b = {}                   # {numero: "agente"|"neutral"|"asesino"} — vista del jugador B
        self.dador_actual = None          # "A" | "B" — quien da la pista en este turno
        self.agentes_revelados = 0
        self.total_agentes_duo = 15
        self.pistas_restantes = 9

