class State(object):
    """Storage object for game state"""
    def __init__(self):
        # estados generales
        self.fase_actual = None       
        self.active_player = None
        self.reviewer_player = None
        self.player_counter = 0
        self.last_votes = {}
        self.removed_votes = {}
        
        # Acciones de la carta actual
        self.acciones_carta_actual = None
        # Marca el indice de la accion que actuialmente se esta ejecutando.
        # Este numero aumenta cuando la opcion actual termino todos sus comandos
        self.index_accion_actual = 0
        # Opcion en caso de que hubiese mas de 1, que se esta ejecutando.
        # Este numero no aumenta, se elije. Si es distinto de 0 es que el jugador ya eligio.
        self.index_opcion_actual = 0
        # Este numero va en aumento hasta que no hay mas comandos que realizar.
        self.index_comando_actual = 0
        self.comando_pedido = False
        self.comando_realizado = False
        self.adquirir_final = False
        # Marca si se esta ejecutando una carta
        self.ejecutando_carta = False        
        # Variables de Lost Expedition
        # Marca si es de dia o de noche
        self.esdedia = True
        # Contador de cuantas cartas se ingresaron del deck (Solo solitario)
        self.count_cartas_deck = 0
        # Cuantas veces se ha mezclado el mazo
        self.amount_shuffled = 0
        # Progreso actual de la expedicion TODO: Esto deberia estar en otra parte para el modo competitivo
        self.progreso = 1
        # Objetivo, creo que es ajustable esto en los modos de dificultad.
        self.objetivoprogreso = 9
        self.swap_cards = []
        
        
        '''
        # Borrar luego al hacer limpieza del bot
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
        '''
