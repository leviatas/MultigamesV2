from Boardgamebox.State import State as BaseState
from BattlestarGalactica.Constants import Space


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
        self.quorum_deck = []             # mazo de Quórum (Presidente)
        self.quorum_discard = []
        self.quorum_pendiente = None      # carta de Quórum esperando elección de objetivo

        # --- Chequeo de habilidad en curso ---
        self.skill_check = None           # dict: {crisis, colores, dificultad, aportes:{uid:[cartas]}, ...}
        self.crisis_vote = None           # dict: {opciones, votos:{uid:idx}} para crisis de voto

        # --- Paso "Recibir Habilidades" en curso (elección de color) ---
        self.skill_draw = None            # dict: {uid, restantes, pool:[colores]}

        # --- Naves: modelo posicional por áreas del espacio ---
        self.areas = [Space.nueva_area() for _ in range(Space.N_AREAS)]
        self.vipers_reserva = 8
        self.vipers_danados = 0           # Vipers dañados (fuera de combate hasta reparar)
        self.nuke_usado = False           # ataque nuclear del Almirante (1 por juego)

        # --- Naves civiles aún no desplegadas (con carga oculta) ---
        self.civiles_pile = []

        # --- Daño a Galactica (6 tokens = destruida → derrota humana) ---
        self.galactica_danos = 0
        self.galactica_danos_max = 6

        # --- Abordaje / centuriones en Galactica ---
        self.centuriones = 0              # avance del abordaje
        self.centuriones_max = 4          # al llegar, Galactica es tomada (Cylons ganan)

        # --- Cylons revelados ---
        self.cylons_revelados = []        # uids

        # --- Resultado ---
        self.ganador = None               # "Humanos" | "Cylons" | None
        self.razon_fin = None

    # --- Totales derivados del modelo posicional de naves ---
    def total_raiders(self):
        return sum(a["raiders"] for a in self.areas)

    def total_basestars(self):
        return sum(len(a["basestars"]) for a in self.areas)

    def total_vipers_espacio(self):
        return sum(a["vipers"] for a in self.areas)

    def total_civiles(self):
        return sum(len(a["civiles"]) for a in self.areas)
