from Boardgamebox.State import State as BaseState

class State(BaseState):
    """Storage object for game state"""
    def __init__(self):
        BaseState.__init__(self)
        self.mayor = None                
        self.preguntas_restantes = 20        
        self.muy_lejos = True
        self.muy_cerca = True
        self.correcto = True
        self.last_votes = {}
        self.preguntas_pendientes = []
        self.warning = 60
        self.aprendiz_vidente = False
        self.aprendiz_adivinadora = False

