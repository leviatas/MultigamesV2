from Boardgamebox.State import State as BaseState

class State(BaseState):
    """Storage object for game state"""
    def __init__(self):
        BaseState.__init__(self)
        self.day = 1 # Indica el día actual, la primera noche es especial
        self.phase = 'Noche' # El juego comienza de noche
        self.can_nominate = False # Al comenzar no se puede acusar esto sera habilitadon con un comando
        self.accuser = None # Jugador que acuso
        self.defender = None # Jugador que fue acusado
        self.accusation = None # Acusacion del acusafor
        self.defense = None # Defenss del acusado
        self.votes = {}
        self.clock = -1 # Marca que jugador debe votar -1 es para que de tiempo al ST a iniciar o al defensor a dar defensa
        self.chopping_block_votes = 0
        self.chopping_block = None