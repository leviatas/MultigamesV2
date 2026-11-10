from Boardgamebox.State import State as BaseState


class Corredor(object):
    """Un corredor en la pista durante una carrera."""

    def __init__(self, rid, uid):
        self.rid = rid
        self.uid = uid
        self.pos = 0
        # Casilla más adelantada que alcanzó (para el Baboso)
        self.max_pos = 0
        self.tropezado = False
        # 1 o 2 si llegó a la meta, None si sigue corriendo
        self.lugar = None
        self.eliminado = False
        # Poderes que tiene (ids de CORREDORES). Normalmente solo el suyo, pero el
        # Cambiante, el Heredero, el Suplente, el Mutante o el Impostor los cambian.
        self.poderes = [rid]
        # Marcas de "una vez por carrera" y elecciones previas ya hechas
        self.usados = []
        # La Bestia ya se transformó
        self.bestia = False
        # Índice del corredor elegido por el Estratega / el Alma Gemela
        self.prediccion = None
        self.alma = None


class State(BaseState):
    def __init__(self):
        BaseState.__init__(self)
        # Configurando -> Draft -> Eleccion -> Largando -> Carrera -> (Eleccion ...) -> Finalizado
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
        self.trampas = []         # (sin uso: compatibilidad con la imagen de la pista)
        self.ultima_tirada = None
        self.llegadas = []        # índices de corredores en orden de llegada
        self.log = []             # relato del turno en curso
        self.ganadores_uids = []
        # uid del dueño del corredor que terminó más atrás (larga la próxima carrera)
        self.rezagado_uid = None
        self.ultimo_primer_jugador = None

        # Índice del corredor que monta el jabalí (Jinete Jabalí), o None
        self.jabali = None
        # El Cancelador canceló la carrera
        self.cancelada = False
        # Marinero: índice del corredor que juega a continuación, y desde dónde se retoma
        self.siguiente_forzado = None
        self.reanudar = None
        # Índice del corredor que ya jugó un turno extra seguido (no encadena otro)
        self.extra_de = None
        # rids de los ganadores (oro) de las carreras anteriores (para el Heredero)
        self.campeones = []
