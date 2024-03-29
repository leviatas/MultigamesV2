from Boardgamebox.Player import Player as BasePlayer

class Player(BasePlayer):
    def __init__(self, name, uid, nick):
        BasePlayer.__init__(self, name, uid)
        self.nick = nick # Nick del usuario (El @leviatas por ej)
        self.role = "" # Ej: Drunk
        self.afiliation = "" # Good or Evil
        self.team = "" # Indica cual de los subgrupos es el jugador townfolk_Outsider_Minion_Demon_Traveller
        self.poisoned = False # Indica si el jugador esta envenenado
        self.drunk = False # Indica si el jugador esta borracho
        self.nominated_someone = False # Indica si nominaste a alguien esta ronda
        self.was_nominated = False # Indica si fue nominado
        self.has_voted = False # Indica si has votado
        self.dead = False # Indica si has muerto
        self.has_last_vote = True # Indica si el jugador muerto todavia puede votar
        
        self.role_description = "" # Descripcion del rol
        self.whispering = [] # Con quien esta hablando el jugador actualmente
        self.whispering_count = 0 # Cantidad de whispers que he realizado en el dia
        self.notes = []
        self.reminders = []

    def get_private_info(self, game):
        board = "--- Info del Jugador {} en la partida *{}*---\n".format(self.name, game.groupName) 
        return board