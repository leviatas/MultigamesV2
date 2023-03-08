# Base Board
from Boardgamebox.Board import Board as BaseBoard
from BloodClocktower.Boardgamebox.State import State
from BloodClocktower.Constants import playerSets

import math


# import logging as log

# log.basicConfig(
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     level=log.INFO)
# logger = log.getLogger(__name__)

class Board(BaseBoard):
    def __init__(self, playercount):
        self.state = State()
        self.num_players = playercount
    
    def getIndex(self, li, player): 
        for index, x in enumerate(li): 
            if x.uid == player.uid: 
                return index 
        return -1
    	
    def starting_with(self, lst, player):
        index = self.getIndex(lst, player)
        # log.info(index)
        start = index+1 if index is not len(lst)-1 else 0
        for idx in range(len(lst)):
            yield  lst[(idx + start) % len(lst)]

    def player_call(self, player):
        return "[{0}](tg://user?id={1})".format(player.name, player.uid)

    def print_board(self, game):
        roles = list(playerSets[self.num_players]["roles"])
        townfolk = roles.count("Townfolk")
        outsiders = roles.count("Outsiders")
        minions = roles.count("Minions")
        demons = roles.count("Demons")
        state = game.board.state

        if game.storyteller is None:
            return "¡¡El juego no tiene Storyteller todvia!! Conviertete en él poniendo /storyteller"

        board = ""
        #board += f"Dia {state.day}: {state.phase}\n"
        jugadores = len(game.player_sequence)
        vivos = game.count_alive()
        votos = game.count_votes()
        
        board += f"{state.phase} {state.day}\n"
        board += f"👤 {jugadores} Jugadores\n❤ {vivos} Vivos\n🗳 {votos} Votos totales\n"
        board += "💀 Muerto con voto\n"
        board += "☠️ Muerto sin voto\n"
        board += f"{townfolk}💙 {outsiders}💚 {minions}🧡 {demons}❤️\n\n"

        if state.accuser is not None:
            positivos = list(state.votes.values()).count("si")
            necesarios = max(math.ceil(vivos/2), state.chopping_block_votes + 1)
            board += f"*{state.accuser.name}* nominó a *{state.defender.name}* ({positivos}/{necesarios} votos necesarios para llevarlo al chopping block)\n\n"
            board += f"*Acusación*: {state.accusation}\n\n"
            board += f"*Defensa*: {state.defense}\n\n"

        lista = game.player_sequence if state.accuser is None else self.starting_with(game.player_sequence, state.defender)
        
        for index, player in enumerate(lista):
            nombre = player.name.replace("_", " ") if state.clock is not index else self.player_call(player)
            num_whisper = "" if player.whispering_count == 0 else player.whispering_count

            chop = f"🪓 {state.chopping_block_votes}" if state.chopping_block is not None and state.chopping_block.uid == player.uid else ""
            clock = "➡️ " if state.clock == index else ""
            accuser = "🫵" if state.accuser != None and player.uid == state.accuser.uid else "" 
            dead = ('💀' if player.has_last_vote else '☠️') if player.dead else ""
            voted = "✋" if player.uid in state.votes and state.votes[player.uid] == "si" else ""
            board += f"{clock}{nombre} {chop}{dead}{accuser} {voted}\n"
        
        # Si estan abiertas la snominaciones y nadie acuso
        if state.can_nominate and state.accuser is None:
            board += "\n*Las nominaciones están abiertas*"
        # Si falta la defensa
        elif state.accuser is not None and state.defense is None:
            board += f"{self.player_call(state.defender)} debes dar tu defensa, para hacer haz /defense Defensa"
        # Si estamos en el momento de votar
        elif state.accuser is not None and state.defense is not None:
            board += "\n/vote - votar ✋\n/clearvote - eliminar el voto\n/tick - pasar el turno al siguiente jugador"
        
        return board
        