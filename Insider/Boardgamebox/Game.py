from Boardgamebox.Game import Game as BaseGame
from Insider.Boardgamebox.Player import Player
from Insider.Boardgamebox.Board import Board


class Game(BaseGame):
    def __init__(self, cid, initiator, groupName, tipo=None, modo=None):
        BaseGame.__init__(self, cid, initiator, groupName, tipo, modo)

    def add_player(self, uid, name):
        self.playerlist[uid] = Player(name, uid)

    def create_board(self):
        self.board = Board(len(self.playerlist), self)

    def get_rules(self):
        return [
            "Insider",
            "Uno de los jugadores es el *Guía* (conocido por todos) y secretamente "
            "elige una palabra. Uno de los demás es el *Infiltrado*, que también "
            "conoce la palabra e intentará guiar la conversación sin ser descubierto. "
            "El resto son *Ciudadanos*.\n\n"
            "*Fase 1 — Preguntas:* todos hacen preguntas de sí/no al Guía para adivinar "
            "la palabra secreta antes de que se acabe el tiempo. El Infiltrado ayuda "
            "disimuladamente. Cuando alguien acierta, el Guía marca quién fue con "
            "`/acerto`. Si nadie acierta a tiempo, el Guía usa `/notiempo` y todos pierden.\n\n"
            "*Fase 2 — Juzgar:* todos votan si el que acertó es el Infiltrado.\n"
            "*Fase 3 — Votar:* si no hay mayoría, todos señalan a quién creen el Infiltrado.\n\n"
            "*Comandos:*\n"
            "• `/acerto` — (Guía) marcar quién adivinó la palabra\n"
            "• `/notiempo` — (Guía) se acabó el tiempo, nadie acertó\n"
            "• `/palabra` — (Guía/Infiltrado) ver la palabra secreta\n"
            "• `/mirol` — ver tu rol en privado\n\n"
            "*Victoria:*\n"
            "• Guía y Ciudadanos: descubren al Infiltrado\n"
            "• Infiltrado: no es descubierto (o nadie adivina la palabra)"
        ]

    async def call(self, context):
        import Insider.Commands as InsiderCommands
        if self.board is not None:
            await InsiderCommands.command_call(context.bot, self)
