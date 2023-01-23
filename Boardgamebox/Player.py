class Player(object):
        def __init__(self, name, uid):
                self.name = name
                self.uid = uid
                
        def get_private_info(self, game):
                board = "--- Info del Jugador {} ---\n".format(self.name)                
                return board
