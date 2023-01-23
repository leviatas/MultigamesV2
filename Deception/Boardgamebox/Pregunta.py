

class Pregunta(object):
    """Storage object for game state"""
    def __init__(self, uid, pregunta, orden):
        # Usuario que hizo la pregunta
        self.uid = uid
        # La pregunta en si.
        self.pregunta = pregunta
        # La respuesta      
        self.respuesta = None
        # orden de la pregunta.
        self.orden = orden