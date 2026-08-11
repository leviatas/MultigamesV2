from Boardgamebox.Game import Game as BaseGame
from Flip7.Boardgamebox.Player import Player
from Flip7.Boardgamebox.Board import Board


class Game(BaseGame):
    def __init__(self, cid, initiator, groupName, tipo=None, modo=None):
        BaseGame.__init__(self, cid, initiator, groupName, tipo, modo)

    def add_player(self, uid, name):
        self.playerlist[uid] = Player(name, uid)

    def create_board(self):
        self.board = Board(len(self.playerlist), self)

    async def call(self, context):
        import Flip7.Commands as Flip7Commands
        if self.board is not None:
            await Flip7Commands.command_call(context.bot, self)

    def get_rules(self):
        return [
            "Flip 7",
            "Todas las cartas del mazo son públicas: no hay información secreta.\n\n"
            "En cada ronda, los jugadores van tirando por turno. En tu turno elegís con los "
            "botones *Pedir carta* (robás una carta y se suma a tu mesa) o *Plantarte* "
            "(guardás los puntos que ya tenés en la ronda).\n\n"
            "Si robás un número que ya tenías en la ronda, *revientas* y perdés todos los "
            "puntos de esa ronda, salvo que tengas una carta *Segunda Oportunidad* guardada "
            "(se descarta y te salva).\n\n"
            "Si juntás *7 números distintos* en la ronda, lográs *¡Flip 7!*, ganás un bonus "
            "de *15 puntos* y la ronda termina inmediatamente para todos.\n\n"
            "Cartas modificadoras (*+2, +4, +6, +8, +10, X2*) se suman a tu puntaje de la "
            "ronda; *X2* duplica la suma de tus cartas numéricas.\n\n"
            "Cartas de acción:\n"
            "• *❄️ Congelar*: elegís a un jugador activo (podés ser vos) para que se plante "
            "de inmediato con lo que ya tiene.\n"
            "• *🔄 Flip Three*: elegís a un jugador activo (podés ser vos) que debe robar 3 "
            "cartas seguidas de forma obligada.\n"
            "• *🍀 Segunda Oportunidad*: te la guardás; si ya tenías una, se la das a otro "
            "jugador activo que no tenga una (o se descarta si no hay nadie disponible).\n\n"
            "La ronda termina cuando todos los jugadores se plantaron, revientaron o se "
            "logró un Flip 7. Gana la partida el primer jugador que llega a *200 puntos* al "
            "final de una ronda (si empatan en la cima, comparten la victoria)."
        ]
