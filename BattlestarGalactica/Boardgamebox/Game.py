from Boardgamebox.Game import Game as BaseGame
from BattlestarGalactica.Boardgamebox.Player import Player
from BattlestarGalactica.Boardgamebox.Board import Board


class Game(BaseGame):
    def __init__(self, cid, initiator, groupName, tipo=None, modo=None):
        BaseGame.__init__(self, cid, initiator, groupName, tipo, modo)

    def add_player(self, uid, name):
        self.playerlist[uid] = Player(name, uid)

    def create_board(self):
        self.board = Board(len(self.playerlist), self)

    def get_rules(self):
        return [
            "Battlestar Galactica",
            "Juego de deducción social cooperativo (con traidores). La flota humana "
            "huye de los Cylons buscando recorrer una *distancia de 8* mediante saltos FTL, "
            "mientras gestiona 4 recursos: 🍞 Comida, ⛽ Combustible, 🙂 Moral y 👥 Población.\n\n"
            "Cada jugador es un *personaje* (Político, Militar, Piloto o Apoyo). En secreto, "
            "algunos jugadores son *Cylons* (cartas de lealtad repartidas por privado) y sabotean "
            "a la flota. A mitad de camino (distancia 4) ocurre la *Fase del Agente Durmiente*: "
            "se reparte otra carta de lealtad.\n\n"
            "*Turno:* Recibir Habilidades → Movimiento → Acción → Crisis. Las crisis se resuelven "
            "con *chequeos de habilidad* (los jugadores aportan cartas boca abajo + 2 cartas de "
            "Destino, comparando contra una dificultad).\n\n"
            "*Victoria humana:* alcanzar la distancia 8 con todos los recursos por encima de 0.\n"
            "*Victoria Cylon:* que cualquier recurso llegue a 0, o la población se agote, o "
            "Galactica sea abordada/destruida."
        ]

    async def call(self, context):
        import BattlestarGalactica.Commands as BSGCommands
        if self.board is not None:
            await BSGCommands.command_call(context.bot, self)
