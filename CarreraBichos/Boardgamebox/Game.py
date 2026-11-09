from Boardgamebox.Game import Game as BaseGame
from CarreraBichos.Boardgamebox.Player import Player
from CarreraBichos.Boardgamebox.Board import Board
from CarreraBichos.Constants.Cartas import (
    CANTIDAD_CARRERAS, DINERO_INICIAL, PAGOS_GANADOR, PAGOS_PODIO, MULTA_FUERTE, AYUDA_CARTAS,
    LARGO_PISTA,
)


class Game(BaseGame):
    def __init__(self, cid, initiator, groupName, tipo=None, modo=None):
        BaseGame.__init__(self, cid, initiator, groupName, tipo, modo)

    def add_player(self, uid, name):
        self.playerlist[uid] = Player(name, uid)

    def create_board(self):
        self.board = Board(len(self.playerlist), self)

    def apuestas_por_jugador(self):
        return 3 if len(self.playerlist) == 2 else 2

    async def call(self, context):
        import CarreraBichos.Commands as CBCommands
        if self.board is not None:
            await CBCommands.command_call(context.bot, self)

    def get_rules(self):
        return [
            "🏟️ *Carrera de Bichos*\n\n"
            "Cuatro bichos corren y ustedes apuestan. Se juegan *{} carreras*; cada uno "
            "empieza con *${}* y gana quien termine con más plata.\n\n"
            "*1. Apuestas:* por turnos (en serpiente) cada uno toma {} boletos:\n"
            "• 🏆 *Ganador*: el bicho sale 1°. Pagos {}.\n"
            "• 🥈 *Podio*: el bicho sale 1° o 2°. Pagos {}.\n"
            "• ❓ *Especial*: una pregunta de SÍ/NO sobre la carrera.\n"
            "El primero en tomar un boleto se lleva el mejor pago. Cada boleto se juega "
            "*normal* (si pierde no pasa nada) o *🔥 fuerte* (cobra el doble, pero si pierde "
            "paga ${}).\n\n"
            "*2. Aportes:* todos ven el mazo base. Cada uno elige en secreto una carta de su "
            "mano y la mete al mazo. 🤫\n\n"
            "*3. ¡Carrera!* Se queman 3 cartas y se dan vuelta de a una, en vivo. La pista "
            "tiene {} casillas; termina cuando 2 bichos cruzan la meta (los demás quedan "
            "ordenados por posición). Si el mazo se acaba se mezcla y se sigue.\n\n"
            "*Cartas:*\n{}\n\n"
            "En la última carrera todos los pagos (¡y multas!) son dobles.".format(
                CANTIDAD_CARRERAS, DINERO_INICIAL, self.apuestas_por_jugador() if self.playerlist else 2,
                "/".join("${}".format(p) for p in PAGOS_GANADOR),
                "/".join("${}".format(p) for p in PAGOS_PODIO),
                MULTA_FUERTE, LARGO_PISTA, AYUDA_CARTAS
            )
        ]
