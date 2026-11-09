from Boardgamebox.Game import Game as BaseGame
from GranPremioArcano.Boardgamebox.Player import Player
from GranPremioArcano.Boardgamebox.Board import Board
from GranPremioArcano.Constants.Corredores import (
    LARGO_PISTA, PUNTOS_ORO, PUNTOS_PLATA, CANTIDAD_CARRERAS, DESCRIPCION_CASILLA
)


class Game(BaseGame):
    def __init__(self, cid, initiator, groupName, tipo=None, modo=None):
        BaseGame.__init__(self, cid, initiator, groupName, tipo, modo)

    def add_player(self, uid, name):
        self.playerlist[uid] = Player(name, uid)

    def create_board(self):
        self.board = Board(len(self.playerlist), self)

    def corredores_por_carrera(self):
        # Con 2 jugadores cada uno corre con 2 corredores por carrera.
        return 2 if len(self.playerlist) == 2 else 1

    async def call(self, context):
        import GranPremioArcano.Commands as GPCommands
        if self.board is not None:
            await GPCommands.command_call(context.bot, self)

    def get_rules(self):
        return [
            "🏆 *Gran Premio Arcano*\n\n"
            "Cada jugador arma un equipo de corredores con poderes que rompen las reglas y "
            "los hace correr en *{} carreras* (cada corredor corre una sola vez).\n\n"
            "*Equipo:* se arma por draft (se revelan 2 cartas por jugador y se eligen en "
            "serpiente) o al azar. Con 2 jugadores cada uno usa 2 corredores por carrera.\n\n"
            "*Antes de cada carrera* cada uno elige en privado qué corredor manda, y se "
            "revelan todos juntos.\n\n"
            "*Tu turno:* tocás 🎲 y se tira el dado de Telegram; tu corredor avanza eso "
            "(tu *tirada*). Algunos poderes te dan opciones en vez de tirar.\n"
            "• *Adelantar*: empezar un movimiento detrás de alguien y terminarlo delante.\n"
            "• *Tropezar* 💫: el corredor pierde su próxima tirada.\n"
            "• *Teletransportar* ✨: se pone en otra casilla sin moverse (no adelanta a nadie).\n\n"
            "La pista tiene {} casillas. La *carrera termina* apenas el segundo corredor "
            "cruza la meta. 🥇 Oro: {} puntos según la carrera; 🥈 Plata: {}.\n\n"
            "Las carreras 2 y 4 son en la 🌋 *Pista Salvaje*: {}.\n\n"
            "Después de la carrera {} gana quien sume más puntos.".format(
                CANTIDAD_CARRERAS, LARGO_PISTA,
                "/".join(str(p) for p in PUNTOS_ORO), "/".join(str(p) for p in PUNTOS_PLATA),
                ", ".join(DESCRIPCION_CASILLA.values()), CANTIDAD_CARRERAS
            )
        ]
