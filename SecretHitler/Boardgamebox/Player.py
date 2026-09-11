class Player(object):
    def __init__(self, name, uid):
        self.name = name
        self.uid = uid
        self.role = None
        self.party = None
        self.is_dead = False
        # uid del presidente que lo ejecuto, o None si sigue vivo o murio por otra via
        self.killed_by_uid = None
        self.inspected_players = {}
        self.was_investigated = False
        #"Liberal","Fascista","Hitler"
        self.preference_rol = ""
        # Si esta activo, el jugador vota Ja automaticamente apenas se propone una formula (fuera de Zona Hitler)
        self.auto_ja = False
        # Solo modo socialista: lo convirtio el poder de Reclutamiento. Cambia la afiliacion,
        # nunca el rol.
        self.was_recruited = False

    def party_efectiva(self):
        # Con quien gana este jugador. Normalmente es su afiliacion, pero Hitler gana siempre
        # con los fascistas "regardless of your Party Membership card": aunque lo recluten y
        # pase a tener carta socialista, sigue siendo fascista para ganar, para los despertares
        # socialistas y para las estadisticas. Lo unico que cambia es lo que ve quien lo investiga.
        if self.role == "Hitler":
            return "fascista"
        return self.party

    def get_private_info(self, game):
        board = "--- *Info del Jugador {}* ---\n".format(self.name)
        board += "Eres *{}* y tu afiliacion es *{}*\n".format(self.role, self.party)
        board += "Voto automático Ja (/startautoja): *{}*\n".format("Activado" if getattr(self, 'auto_ja', False) else "Desactivado")
        player_number = len(game.playerlist)
        es_socialista = game.es_socialista()
        if self.role == "Fascista":
            fascists = game.get_fascists()
            # En el modo socialista los fascistas siempre se conocen entre si, porque el
            # reglamento de la expansion manda usar las instrucciones de una partida de 7.
            if player_number > 6 or es_socialista:
                fstring = ""
                for f in fascists:
                    if f.uid != self.uid:
                        fstring += f.name + ", "
                fstring = fstring[:-2]
                if not game.is_debugging:
                    board += "Tus compañeros fascistas son: *{}*\n".format(fstring)
            hitler = game.get_hitler()
            board += "Hitler es: *{}*".format(hitler.name)
        elif self.role == "Hitler":
            # En el modo socialista Hitler nunca conoce a nadie, ni en partidas chicas.
            if player_number <= 6 and not es_socialista:
                fascists = game.get_fascists()
                board +=  "Tu compañero fascista es: *{}*".format(fascists[0].name)
        elif self.role == "Socialista":
            companeros = [s.name for s in game.get_socialists() if s.uid != self.uid]
            if not companeros:
                board += "Sos el único socialista de origen de la partida."
            elif not game.is_debugging:
                board += "Tus compañeros socialistas son: *{}*".format(", ".join(companeros))
        if getattr(self, "was_recruited", False):
            if self.role == "Hitler":
                board += ("\n\n\u270A Los socialistas te *reclutaron*, pero sos Hitler: no te hace efecto. "
                          "Seguís ganando con los fascistas y no participás de sus decisiones. "
                          "Eso sí, ahora tenés la carta socialista, así que quien te investigue va a ver *socialista*.")
            else:
                board += "\n\n\u270A Fuiste *reclutado por los socialistas*: ahora ganás con ellos."
        return board
