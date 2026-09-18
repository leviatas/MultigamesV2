from SecretHitler.Constants.Config import CORTES_AUTOJA, CORTE_AUTOJA_DEFAULT, POLITICAS_PARA_CORTAR_AUTOJA
from SecretHitler.i18n import t, role_name, party_name


def texto_corte_autoja(corte, ctx=None):
    # Como se le explica a un jugador cuando deja de aplicarse su voto automatico Ja.
    return t("autoja.corte.%s" % corte, ctx, cantidad=POLITICAS_PARA_CORTAR_AUTOJA)


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
        # Si esta activo, el jugador vota Ja automaticamente apenas se propone una formula
        self.auto_ja = False
        # Cuando deja de aplicarse ese voto automatico: "fascistas" (Zona Hitler), "politicas"
        # (cierta cantidad de politicas promulgadas) o "ambas" (cualquiera de las dos, default).
        # Ver MainController.CORTES_AUTOJA.
        self.auto_ja_corte = "ambas"
        # Solo modo socialista: lo convirtio el poder de Reclutamiento. Cambia la afiliacion,
        # nunca el rol.
        self.was_recruited = False

    def corte_autoja(self):
        # Cuando se corta el voto automatico Ja de este jugador. getattr + validacion porque
        # las partidas guardadas antes de que el criterio fuera configurable no tienen el campo.
        corte = getattr(self, "auto_ja_corte", CORTE_AUTOJA_DEFAULT)
        return corte if corte in CORTES_AUTOJA else CORTE_AUTOJA_DEFAULT

    def party_efectiva(self):
        # Con quien gana este jugador. Normalmente es su afiliacion, pero Hitler gana siempre
        # con los fascistas "regardless of your Party Membership card": aunque lo recluten y
        # pase a tener carta socialista, sigue siendo fascista para ganar, para los despertares
        # socialistas y para las estadisticas. Lo unico que cambia es lo que ve quien lo investiga.
        if self.role == "Hitler":
            return "fascista"
        return self.party

    def get_private_info(self, game):
        board = t("info.header", game, nombre=self.name) + "\n"
        board += t("info.role_and_party", game,
                   rol=role_name(self.role, game), afiliacion=party_name(self.party, game)) + "\n"
        if getattr(self, 'auto_ja', False):
            board += t("info.autoja_on", game, corte=texto_corte_autoja(self.corte_autoja(), game)) + "\n"
        else:
            board += t("info.autoja_off", game) + "\n"
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
                    board += t("info.fascist_teammates", game, nombres=fstring) + "\n"
            hitler = game.get_hitler()
            board += t("info.hitler_is", game, nombre=hitler.name)
        elif self.role == "Hitler":
            # En el modo socialista Hitler nunca conoce a nadie, ni en partidas chicas.
            if player_number <= 6 and not es_socialista:
                fascists = game.get_fascists()
                board += t("info.your_fascist_partner", game, nombre=fascists[0].name)
        elif self.role == "Socialista":
            companeros = [s.name for s in game.get_socialists() if s.uid != self.uid]
            if not companeros:
                board += t("info.only_socialist", game)
            elif not game.is_debugging:
                board += t("info.socialist_teammates", game, nombres=", ".join(companeros))
        if getattr(self, "was_recruited", False):
            if self.role == "Hitler":
                board += "\n\n" + t("info.recruited_hitler", game)
            else:
                board += "\n\n" + t("info.recruited", game)
        return board
