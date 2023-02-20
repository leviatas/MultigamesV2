from Boardgamebox.State import State as BaseState

class State(BaseState):
    """Storage object for game state"""
    def __init__(self):
        BaseState.__init__(self)
        self.day = 0 # Indica el día actual, la primera noche es especial
        self.phase = 'Noche' # El juego comienza de noche
        self.can_accuse = False # Al comenzar no se puede acusar esto sera habilitadoncon un comando
        self.accuser = None # Jugador que acuso
        self.defender = None # Jugador que fue acusado
        self.accusation = None # Acusacion del acusafor
        self.defense = None # Defenss del acusado
        self.votes = {}