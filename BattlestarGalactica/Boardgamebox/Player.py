from Boardgamebox.Player import Player as BasePlayer


class Player(BasePlayer):
    def __init__(self, name, uid):
        BasePlayer.__init__(self, name, uid)
        self.personaje = None          # clave del personaje elegido
        self.tipo = None               # Politico/Militar/Piloto/Apoyo
        self.ubicacion = None          # clave de ubicación actual
        self.titulos = []              # ["Presidente"] / ["Almirante"]
        self.loyalty_cards = []        # lista de strings (cylon/humano/simpatizante)
        self.is_cylon = False          # revelado o no, refleja si tiene carta cylon
        self.revealed = False          # si ya se reveló como Cylon
        self.skill_hand = []           # lista de cartas {color, valor}
        self.quorum_hand = []          # cartas de Quórum (Presidente)
        self.en_calabozo = False
        self.habilidad_usada = False   # habilidad de "una vez por juego"
        self.viper_area = None         # índice de área si pilota un Viper (None = en una ubicación)
