class State(object):
    """Storage object for game state"""
    def __init__(self):
        self.liberal_track = 0
        self.fascist_track = 0
        self.failed_votes = 0
        self.president = None
        self.nominated_president = None
        self.nominated_chancellor = None
        self.chosen_president = None
        self.chancellor = None
        self.dead = 0
        self.last_votes = {}
        self.game_endcode = 0
        self.drawn_policies = []
        self.player_counter = 0
        self.veto_refused = False
        self.not_hitlers = []
        self.currentround = -1
        self.votes_anarquia = {}
        self.fase = None
        # --- Solo modo socialista (ver Game.modo) ---
        self.socialist_track = 0
        # Presidente de la Camara: lo elige el canciller despues de una votacion exitosa
        # y espia la primera politica del mazo. Deja de existir cuando se activa la Censura.
        self.chairman = None
        # uids elegidos por el poder de Reclutamiento, en orden (incluye el intento fallido
        # sobre Hitler, que sigue siendo fascista: el Congreso lo usa para avisar que fallo).
        # Es una lista y no un dict a proposito: jsonpickle convierte las claves de los dicts
        # a string y habria que castearlas de nuevo al cargar la partida.
        self.recruited_uids = []
        # Poder socialista ofrecido y todavia sin resolver.
        self.pending_socialist_power = None
        # Propuesta socialista en votacion: cualquier socialista vivo propone un objetivo y
        # el resto vota; se aplica solo por unanimidad. None cuando no hay ninguna en curso
        # (ahi es cuando se puede proponer). Las claves son strings y los uids van en una
        # lista, asi jsonpickle no los convierte a string al guardar la partida.
        # {"power": str, "target": uid, "proposer": uid, "approvals": [uid, ...]}
        self.socialist_proposal = None
