from Boardgamebox.Game import Game as BaseGame
from PuertoBanana.Boardgamebox.Player import Player
from PuertoBanana.Boardgamebox.Board import Board


class Game(BaseGame):
    def __init__(self, cid, initiator, groupName, tipo=None, modo=None):
        BaseGame.__init__(self, cid, initiator, groupName, tipo, modo)

    def add_player(self, uid, name):
        self.playerlist[uid] = Player(name, uid)

    def create_board(self):
        self.board = Board(len(self.playerlist), self)

    def get_rules(self):
        return [
            "Puerto Banana",
            "Todos los jugadores empiezan con *10 bananas*, anotadas en su tablero "
            "privado (usá `/info` para ver tu cantidad). El juego termina cuando algún "
            "jugador llega a *200 bananas*.\n\n"
            "En cada ronda se subasta un pozo que equivale a la cantidad de bananas que "
            "tiene el jugador que va ganando. Cada jugador puja en privado con "
            "`/puja CANTIDAD` cualquier cantidad que quiera, en secreto, sin estar "
            "limitado por lo que tiene.\n\n"
            "El jugador que pujó más alto se lleva el pozo, pero en vez de pagar lo que "
            "pujó, paga al segundo jugador que pujó más alto la *diferencia* entre ambas "
            "pujas.\n\n"
            "Si esa diferencia es mayor a lo que el jugador puede pagar (sumando lo que "
            "tenía más lo ganado en el pozo), queda *eliminado de la ronda* y pierde "
            "todas sus bananas.\n\n"
            "*Comandos:*\n"
            "• `/puja CANTIDAD` — pujar en privado\n"
            "• `/info` — ver cuántas bananas tenés"
        ]

    async def call(self, context):
        import PuertoBanana.Commands as PuertoBananaCommands
        if self.board is not None:
            await PuertoBananaCommands.command_call(context.bot, self)
