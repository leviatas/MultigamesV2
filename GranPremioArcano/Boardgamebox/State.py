from Boardgamebox.State import State as BaseState


class Corredor(object):
    """Un corredor en la pista durante una carrera."""

    def __init__(self, rid, uid):
        self.rid = rid
        self.uid = uid
        self.pos = 0
        self.tropezado = False
        # 1 o 2 si llegó a la meta, None si sigue corriendo
        self.lugar = None
        # Poderes de "una vez por carrera" ya usados (lista de strings)
        self.usados = []
        # Posición al empezar el turno actual (para la Araña)
        self.pos_inicio_turno = 0


class State(BaseState):
    def __init__(self):
        BaseState.__init__(self)
        # Configurando -> Draft -> Eleccion -> Carrera -> (Eleccion ... ) -> Finalizado
        self.fase_actual = "Configurando"
        self.carrera = 1
        self.reparto = None  # "draft" | "azar"

        # --- Draft ---
        self.mazo = []
        self.draft_ronda = 0
        self.draft_total_rondas = 0
        self.draft_cartas = []
        self.draft_orden = []  # uids en orden de elección (snake)
        self.draft_idx = 0
        self.draft_msg_id = None

        # --- Carrera ---
        self.corredores = []      # lista de Corredor
        self.orden_turnos = []    # índices en self.corredores
        self.turno_idx = 0
        self.turno_n = 0          # contador global para invalidar botones viejos
        # Accion | Objetivo | PostTirada | Procesando
        self.subfase = None
        # Datos del turno en curso (solo claves string)
        self.pendiente = {}
        self.trampas = []         # casillas con telaraña
        self.ultima_tirada = None # último dado sacado por cualquier corredor (para el Espejo)
        self.llegadas = []        # índices de corredores en orden de llegada
        self.log = []             # relato del turno en curso
        self.ganadores_uids = []
        # uid del dueño del corredor que terminó más atrás (larga la próxima carrera)
        self.rezagado_uid = None
        self.ultimo_primer_jugador = None
