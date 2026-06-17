from Boardgamebox.State import State as BaseState


class State(BaseState):
    def __init__(self):
        BaseState.__init__(self)
        self.fase_actual = "Seleccion de Personajes"

        # --- Recursos (valores iniciales del juego base) ---
        self.comida = 8
        self.combustible = 8
        self.moral = 10
        self.poblacion = 12

        # --- Pistas ---
        self.distancia = 0          # objetivo: 8
        self.objetivo_distancia = 8
        self.jump_prep = 0          # 0..4; en 4 hay autojump
        self.jump_prep_max = 4

        # --- Títulos ---
        self.presidente_uid = None
        self.almirante_uid = None

        # --- Selección de personajes ---
        self.personajes_elegidos = {}     # uid -> clave personaje
        self.orden_seleccion = []         # uids en orden de elegir
        self.indice_seleccion = 0

        # --- Lealtad ---
        self.loyalty_deck = []            # cartas no repartidas
        self.sleeper_hecho = False

        # --- Mazos ---
        self.skill_decks = {}             # color -> lista de cartas
        self.skill_discards = {}          # color -> lista de descartes
        self.destiny_deck = []            # cartas de destino (mezcla de colores)
        self.crisis_deck = []
        self.crisis_discard = []
        self.crisis_actual = None         # dict de la crisis en curso
        self.super_crisis_deck = []       # mazo de súper crisis (Cylons revelados)

        # --- Chequeo de habilidad en curso ---
        self.skill_check = None           # dict: {crisis, colores, dificultad, aportes:{uid:[cartas]}, ...}

        # --- Naves ---
        self.vipers_reserva = 8
        self.vipers_espacio = 0
        self.vipers_danados = 0
        self.raiders = 0
        self.basestars = 0
        self.basestar_hits = 0            # impactos acumulados sobre basestars
        self.nuke_usado = False           # ataque nuclear del Almirante (1 por juego)

        # --- Naves civiles (cada una con carga oculta) ---
        self.civiles = []                 # lista de dicts {recurso, cantidad}

        # --- Abordaje / centuriones en Galactica ---
        self.centuriones = 0              # avance del abordaje
        self.centuriones_max = 4          # al llegar, Galactica es tomada (Cylons ganan)

        # --- Cylons revelados ---
        self.cylons_revelados = []        # uids

        # --- Resultado ---
        self.ganador = None               # "Humanos" | "Cylons" | None
        self.razon_fin = None
