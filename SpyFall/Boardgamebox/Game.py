from Boardgamebox.Game import Game as BaseGame
from SpyFall.Boardgamebox.Player import Player
from SpyFall.Boardgamebox.Board import Board


class Game(BaseGame):
    def __init__(self, cid, initiator, groupName, tipo=None, modo=None):
        BaseGame.__init__(self, cid, initiator, groupName, tipo, modo)

    def add_player(self, uid, name):
        self.playerlist[uid] = Player(name, uid)

    def create_board(self):
        self.board = Board(len(self.playerlist), self)

    def get_rules(self):
        return [
            "SpyFall",
            "Uno de los jugadores es el *Espía*. El resto conoce la localidad secreta y su rol.\n\n"
            "Haz preguntas para descubrir quién es el espía, sin revelar la localidad.\n"
            "El espía intenta descubrir la localidad escuchando las respuestas.\n\n"
            "*Comandos:*\n"
            "• `/acusar` — Iniciar votación para descubrir al espía\n"
            "• `/adivinar` — (Solo espía) Adivinar la localidad\n"
            "• `/rol` — Ver tu rol en privado\n\n"
            "*Victoria:*\n"
            "• Espía: Votan por alguien inocente, o el espía adivina la localidad correctamente\n"
            "• No-espías: Identifican al espía en la votación"
        ]

    async def call(self, context):
        import SpyFall.Commands as SpyFallCommands
        if self.board is not None:
            await SpyFallCommands.command_call(context.bot, self)
