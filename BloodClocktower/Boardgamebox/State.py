from Boardgamebox.State import State as BaseState

class State(BaseState):
    """Storage object for game state"""
    def __init__(self):
        BaseState.__init__(self)
        self.day = 0 # Indica el día actual, la primera noche es especial
        self.phase = 'Noche' # El juego comienza de noche
        self.can_accuse = False # Al comenzar no se puede acusar esto sera habilitadoncon un comando