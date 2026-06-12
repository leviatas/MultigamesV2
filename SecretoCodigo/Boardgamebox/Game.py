from Boardgamebox.Game import Game as BaseGame
from Codenames.Boardgamebox.Player import Player
from Codenames.Boardgamebox.Board import Board


class Game(BaseGame):
    def __init__(self, cid, initiator, groupName, tipo=None, modo=None):
        BaseGame.__init__(self, cid, initiator, groupName, tipo, modo)

    def add_player(self, uid, name):
        self.playerlist[uid] = Player(name, uid)

    def create_board(self):
        self.board = Board(len(self.playerlist), self)

    def get_spymaster(self, team: str):
        if team == "Rojo":
            return self.board.state.spymaster_rojo
        return self.board.state.spymaster_azul

    def get_team_players(self, team: str):
        if team == "Rojo":
            return self.board.state.equipo_rojo
        return self.board.state.equipo_azul

    def is_spymaster(self, uid) -> bool:
        sm_r = self.board.state.spymaster_rojo
        sm_a = self.board.state.spymaster_azul
        return (sm_r and sm_r.uid == uid) or (sm_a and sm_a.uid == uid)

    def is_field_operative(self, uid, team: str) -> bool:
        sm = self.get_spymaster(team)
        players = self.get_team_players(team)
        return any(p.uid == uid for p in players) and (not sm or sm.uid != uid)

    # --- Helpers del modo Cooperativo "Dúo" ---
    def get_player_by_label(self, label: str):
        if label == "A":
            return self.board.state.jugador_a
        if label == "B":
            return self.board.state.jugador_b
        return None

    def get_label_by_uid(self, uid):
        if self.board.state.jugador_a and self.board.state.jugador_a.uid == uid:
            return "A"
        if self.board.state.jugador_b and self.board.state.jugador_b.uid == uid:
            return "B"
        return None

    def get_other_player_label(self, label: str) -> str:
        return "B" if label == "A" else "A"

    def get_rules(self):
        if self.modo == "Cooperativo":
            return ["Codenames Dúo: trabajen juntos para encontrar los 15 agentes sin tocar al asesino ni quedarse sin pistas.\n"
                    "Comandos: /hint PALABRA NUMERO (quien da la pista, en privado) | /pick NUMERO (quien adivina, en el grupo) | /endturn"]
        return ["Codenames: adivinen las palabras de su equipo con las pistas del espía.\nComandos: /hint PALABRA NUMERO (espía, en privado) | /pick NUMERO (agentes, en el grupo) | /endturn"]

    async def call(self, context):
        import Codenames.Commands as CodenamesCommands
        if self.board is not None:
            await CodenamesCommands.command_call(context.bot, self)
