from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.ext import (CallbackContext)
import GamesController

from functools import wraps
import jsonpickle
import os
import psycopg2
from psycopg2 import sql
import urllib.parse
import logging as log

from BloodClocktower.Boardgamebox.Game import Game
from BloodClocktower.Boardgamebox.Player import Player
from Constants.Config import ADMIN
from Utils import restricted, player_call

log.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=log.INFO)
logger = log.getLogger(__name__)

urllib.parse.uses_netloc.append("postgres")
url = urllib.parse.urlparse(os.environ["DATABASE_URL"])

commands = [  # command description used in the "help" command
    '/help - Te da informacion de los comandos disponibles',
    '/start - Da un poco de información sobre Secret Hitler',
    '/symbols - Te muestra todos los símbolos posibles en el tablero',
    '/rules - Te da un link al sitio oficial con las reglas de Secret Hitler',
    '/newgame - Crea un nuevo juego o carga un juego previo',
    '/join - Te une a un juego existente',
    '/startgame - Comienza un juego existente cuando todos los jugadores se han unido',
    '/cancelgame - Cancela un juego existente, todos los datos son borrados.',
    '/board - Imprime el tablero actual con la pista liberal y la pista fascista, orden presidencial y contador de elección',
    '/history - Imprime el historial del juego actual',
    '/votes - Imprime quien ha votado',
    '/call - Avisa a los jugadores que se tiene que actuar'    
]

def storyteller(func):
	@wraps(func)
	def wrapped(update, context, *args, **kwargs):
		user_id = update.effective_user.id
		cid = update.message.chat_id		
		game = get_game(cid)

		if user_id != game.storyteller:
			update.effective_message.reply_text("No tienes acceso, ya que no eres el Storyteller")
			return
		return func(update, context, *args, **kwargs)
	return wrapped

def player(func):
	@wraps(func)
	def wrapped(update, context, *args, **kwargs):
		uid = update.effective_user.id
		cid = update.message.chat_id		
		game = get_game(cid)

		# Si no es u jugador o el ST...
		if uid not in game.playerlist and uid != game.storyteller:
			update.effective_message.reply_text("No tienes acceso, ya que no eres jugador o storyteller")
			return
		return func(update, context, *args, **kwargs)
	return wrapped

def command_start(update: Update, context: CallbackContext):
	bot = context.bot

	cid = update.message.chat_id
	bot.send_message(cid,
		     """Este es un bot para jugar Clock On The Bloodtower""")
	command_help(update, context)

def command_help(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	cid = update.message.chat_id
	help_text = "Los siguientes comandos están disponibles:\n"
	for i in commands:
		help_text += i + "\n"
	bot.send_message(cid, help_text)

def get_game(cid) -> Game:
	# Busco el juego actual
	game = GamesController.games.get(cid, None)	
	if game:
		# Si esta lo devuelvo.
		return game
	else:
		# Si no esta lo busco en BD y lo pongo en GamesController.games
		game = load_game(cid)
		if game:
			GamesController.games[cid] = game
			return game
		else:
			None

def load_game(cid):
	conn = psycopg2.connect(
				database=url.path[1:],
				user=url.username,
				password=url.password,
				host=url.hostname,
				port=url.port
			)
	cur = conn.cursor()			
	log.info("Searching Game in DB")
	query = "SELECT * FROM games_blood WHERE id = %s;"
	cur.execute(query, [cid])
	dbdata = cur.fetchone()

	if cur.rowcount > 0:
		log.info("Gane found")
		jsdata = dbdata[3]
		log.info(jsdata)
		#log.info("jsdat = %s" % (jsdata))				
		game = jsonpickle.decode(jsdata)
		
		# For some reason the decoding fails when bringing the dict playerlist and it changes it id from int to string.
		# So I have to change it back the ID to int.				
		temp_player_list = {}		
		for uid in game.playerlist:
			temp_player_list[int(uid)] = game.playerlist[uid]
		game.playerlist = temp_player_list
		
		if game.board is not None and game.board.state is not None:
			temp_last_votes = {}
			for uid in game.board.state.last_votes:
				temp_last_votes[int(uid)] = game.board.state.last_votes[uid]
			game.board.state.last_votes = temp_last_votes

			temp_votes = {}
			for uid in game.board.state.votes:
				temp_votes[int(uid)] = game.board.state.votes[uid]
			game.board.state.votes = temp_votes
		#bot.send_message(cid, game.print_roles())
		conn.close()
		return game
	else:
		log.info("Game Not Found")
		conn.close()
		return None

@player
def command_board(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	game = get_game(cid)
	if game.board:
		board_text = game.board.print_board(game)
		board_message = bot.send_message(cid, board_text, ParseMode.MARKDOWN)
		game.board_message_id = board_message.message_id
		save_game(cid, "Game in join state", game)
	else:
		bot.send_message(cid, "No ha comenzado el juego todavia, para comenzar pone /startgame")

def command_rules(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id	
	msg = """Reglas de Blood on the clocktower
	"""
	bot.send_message(cid, msg, ParseMode.MARKDOWN)

def command_newgame(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	groupName = update.message.chat.title	

	game = get_game(cid)
	groupType = update.message.chat.type
	if groupType not in ['group', 'supergroup']:
		bot.send_message(cid, "Tienes que agregarme a un grupo primero y escribir /newgame allá!")
	elif game:
		bot.send_message(cid, "Hay un juego comenzado en este chat. Si quieres terminarlo escribe /cancelgame!")
	else:
		newGame = Game(cid, update.message.from_user.id, groupName)
		GamesController.games[cid] = newGame
		bot.send_message(cid, "Nuevo juego creado! Cada jugador debe unirse al juego con el comando /join.\nEl storyteller no debe unirse de esta forma, el sera asignado mas tarde\nEl iniciador del juego (o el administrador) pueden unirse tambien y escribir /startgame cuando todos se hayan unido al juego!")

def command_join(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	# I use args for testing. // Remove after?
	groupName = update.message.chat.title
	cid = update.message.chat_id
	groupType = update.message.chat.type
	game = get_game(cid)
	if len(args) <= 0:
		# if not args, use normal behaviour
		fname = update.message.from_user.first_name.replace("_", " ")
		uid = update.message.from_user.id
	else:
		uid = update.message.from_user.id
		if uid == ADMIN[0]:
			for i,k in zip(args[0::2], args[1::2]):
				fname = i.replace("_", " ")
				uid = int(k)
				player = Player(fname, uid)
				game.add_player(uid, player)
				log.info("%s (%d) joined a game in %d" % (fname, uid, game.cid))
				save_game(cid, "Game in join state", game)
	
	if groupType not in ['group', 'supergroup']:
		bot.send_message(cid, "Tienes que agregarme a un grupo primero y escribir /newgame allá!")
	elif not game:
		bot.send_message(cid, "No hay juego en este chat. Crea un nuevo juego con /newgame")
	elif game.board:
		bot.send_message(cid, "El juego ha comenzado. Por favor espera el proximo juego!")
	elif uid in game.playerlist:
		bot.send_message(game.cid, f"Ya te has unido al juego, {fname}!")
	elif len(game.playerlist) >= 10:
		bot.send_message(game.cid, "Han llegado al maximo de jugadores. Por favor comiencen el juego con /startgame!")
	else:
		#uid = update.message.from_user.id		
		try:
			#Commented to dont disturb player during testing uncomment in production
			bot.send_message(uid, f"Te has unido a un juego en {groupName}. Pronto te dire cual es tu rol secreto.")
			# choose_posible_role(bot, cid, uid)

			game.add_player(uid, fname)
			log.info("%s (%d) joined a game in %d" % (fname, uid, game.cid))
			if len(game.playerlist) > 4:
				bot.send_message(game.cid, fname + " se ha unido al juego. Escribe /startgame si este es el último jugador y quieren comenzar con %d jugadores!" % len(game.playerlist))
			elif len(game.playerlist) == 1:
				bot.send_message(game.cid, "%s se ha unido al juego. Hay %d jugador en el juego y se necesita 5-10 jugadores." % (fname, len(game.playerlist)))
			else:
				bot.send_message(game.cid, "%s se ha unido al juego. Hay %d jugadores en el juego y se necesita 5-10 jugadores" % (fname, len(game.playerlist)))
				# Luego dicto los jugadores que se han unido
			jugadoresActuales = "Los jugadores que se han unido al momento son:\n"
			for player in game.playerlist.values():
				jugadoresActuales += f"{player.name}\n"
			bot.send_message(game.cid, jugadoresActuales)
			save_game(cid, "Game in join state", game)
		except Exception:
			bot.send_message(game.cid, f"Jugador {fname} debes ir a @botontheclocktowerbot y darle /start")

def command_startgame(update: Update, context: CallbackContext):
	bot = context.bot	
	uid = update.message.from_user.id
	cid = update.message.chat_id
	
	game = get_game(cid)

	if not game:
		bot.send_message(cid, "No hay juego en este grupo crea un nuevo juego con /newgame")
	elif update.message.from_user.id not in ADMIN and update.message.from_user.id != game.initiator and bot.getChatMember(cid, update.message.from_user.id).status not in ("administrator", "creator"):
		bot.send_message(game.cid, "Solo el creador del juego o un admin puede iniciar con /startgame")	
	elif game.board:
		bot.send_message(cid, "El juego ya empezo!")		
	else:		
		# Verifico si la configuracion ha terminado y se han unido los jugadores necesarios		
		min_jugadores = 5		
		if len(game.playerlist) >= min_jugadores:
			save_game(cid, "Game in starting state", game)
			game.startgame()
			bot.send_message(game.cid, "El Storyteller debe poner aqui el comando /storyteller para ser reconocido como tal")
		else:
			bot.send_message(game.cid, "Falta el numero mínimo de jugadores. Faltan: %s " % (str(min_jugadores - len(game.playerlist))))

def command_storyteller(update: Update, context: CallbackContext):
	bot = context.bot	
	uid = update.message.from_user.id
	cid = update.message.chat_id	
	game = get_game(cid)

	fname = update.message.from_user.first_name.replace("_", " ")

	if game.storyteller is None:
		game.storyteller = uid
		bot.send_message(game.cid, f"El Storyteller es: {fname}, teman por sus vidas Aldeanos!!!")
		game.shuffle_player_sequence()
		bot.send_message(game.cid, f"Jugaremos Trouble Brewing, ya que es el unico modulo que tengo XD")
		bot.send_message(uid, "Eres el storyteller, prepara los roles y cuando quieras reparte los roles")
		bot.send_message(uid, "Con /firstnight en el grupo se hará la primera noche (No hace nada actualmente)")
		bot.send_message(uid, "Con /day comenzarás el primer día y luego con /night pasarás a la noche. Para ir al siguiente dia, pones /day nuevamente.")
	else:
		bot.send_message(game.cid, f"La partida ya tiene storyteller, vete de aquí maldito usurpador!!!")

def command_delete(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	log.info('command_cancelgame called {}'.format(args))
	cid = update.message.chat_id
	uid = update.effective_user.id
	#Always try to delete in DB	
	if len(args) > 0 and uid == ADMIN[0]:
		cid = int(args[0])	
	try:
		delete_game(cid)
		if cid in GamesController.games.keys():
			del GamesController.games[cid]
		bot.send_message(cid, "Borrado exitoso.")
	except Exception as e:
		bot.send_message(cid, "El borrado ha fallado debido a: "+str(e))

@storyteller
def command_firstnight(update: Update, context: CallbackContext):
	bot = context.bot	
	# uid = update.message.from_user.id
	cid = update.message.chat_id
	game = get_game(cid)
	bot.send_message(game.cid, f"Comienza la primera noche, todos... cierren los ojos...")

@storyteller
def command_day(update: Update, context: CallbackContext):
	bot = context.bot	
	cid = update.message.chat_id
	game = get_game(cid)
	game.set_day()
	bot.send_message(game.cid, "Todos, abran los ojos...")
	save_game(cid, "Day", game)
	if game.board.state.day is 1:
		bot.send_message(game.cid, """En el recondito pueblo de ravenswood bluff los aldeanos se despiertan por un grito ahogado en el centro del pueblo, al llegar encuentran a su querido storyteller empelado en una de las manecillas del reloj.

Esto es la obra de un demonio que mata durante la noche, pero durante el día toma la forma de uno de ustedes; su trabajo es encontrarlo y vengar a las almas de los caídos por el.
Mucha suerte""")

@storyteller
def command_night(update: Update, context: CallbackContext):
	bot = context.bot	
	cid = update.message.chat_id
	game = get_game(cid)
	game.set_night()	
	bot.send_message(game.cid, "Todos, cierren los ojos...")
	save_game(cid, "Night", game)

@storyteller
def command_kill(update: Update, context: CallbackContext):
	bot = context.bot	
	args = context.args
	cid = update.message.chat_id
	game = get_game(cid)
	
	if len(args) > 0:
		# Busco el jugador a matar
		player_name = ' '.join(args)
		player = game.find_player(player_name)
		if player is None:
			bot.send_message(game.cid, "El jugador no esta en el partido, recuerda poner el nombre que aparece en el board")
		player.dead = True
		save_game(cid, f"Matamos a {player_name}", game)
		kill_message = f"Jugador {player_name} te han matado, no posees más tu habilidad, pero puedes hablar y votar una última vez"
		game.history.append(kill_message)
		bot.send_message(game.cid, kill_message)
	else:
		bot.send_message(game.cid, f"Debes ingresar a un jugador para matar")

def command_players(update: Update, context: CallbackContext):
	bot = context.bot	
	uid = update.message.from_user.id
	cid = update.message.chat_id
	
	game = get_game(cid)	
	
	if not game:
		bot.send_message(game.cid, "No hay partida en este grupo")
		
	jugadoresActuales = "Los jugadores que se han unido al momento son:\n"
	
	for player in game.playerlist.values():
		jugadoresActuales += f"{player_call(player)}\n"			
	bot.send_message(game.cid, jugadoresActuales, ParseMode.MARKDOWN)

def command_leave(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	uid = update.effective_user.id

	game = get_game(cid)

	if not game:
		bot.send_message(cid, '‼‼*No hay juego del que salir*‼‼', ParseMode.MARKDOWN)
	else:
		if game.board:
			bot.send_message(cid, '‼‼*El juego ya empezo y el admin no permite salir de juegos ya empezados*‼‼', ParseMode.MARKDOWN)
		else:
			del game.playerlist[uid]
			bot.send_message(cid, '‼‼*Has salido exitosamente del juego*‼‼', ParseMode.MARKDOWN)

@player
def command_claim(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	#game.pedrote = 3
	try:
		#Send message of executing command   
		cid = update.message.chat_id
		#Check if there is a current game 
		game = get_game(cid)
		if game:
			uid = update.message.from_user.id
			if uid in game.playerlist or uid is game.storyteller:								
				if len(args) > 0:
					#Data is being claimed
					claimtext = ' '.join(args)
					claimtexttohistory = f"El jugador {game.playerlist[uid].name} declara: {claimtext}"
					bot.send_message(cid, f"Tu declaración: {claimtext} fue agregada al historial.")
					game.history.append(claimtexttohistory)
					log.info(game.history)
					save_game(cid, "Claim", game)
				else:					
					bot.send_message(cid, "Debes mandar un mensaje para hacer una declaración.")

			else:
				bot.send_message(cid, "Debes ser un jugador del partido para declarar algo.")				
		else:
			bot.send_message(cid, "No hay juego en este chat. Crea un nuevo juego con /newgame")
	except Exception as e:
		bot.send_message(cid, str(e))
		log.error("Unknown error: " + str(e))  

def command_showhistory(update: Update, context: CallbackContext):
	bot = context.bot
	#game.pedrote = 3
	try:
		#Send message of executing command   
		cid = update.message.chat_id
		#Check if there is a current game 
		
		groupName = update.message.chat.title

		game = get_game(cid)
		if game:			
			#bot.send_message(cid, "Current round: " + str(game.board.state.currentround + 1))
			uid = update.message.from_user.id
			game.groupName = groupName
			history_text = "Historial del grupo *{}*:\n\n".format(groupName)
			history_textContinue = "" 
			for x in game.history:
				if len(history_text) < 3500:
					history_text += x + "\n\n"
				else:
					history_textContinue += x + "\n\n"

			bot.send_message(uid, history_text, ParseMode.MARKDOWN)
			if len(history_textContinue) > 0:
				bot.send_message(uid, history_textContinue, ParseMode.MARKDOWN)
			#bot.send_message(cid, "I sent you the history to our private chat")			
		else:
			bot.send_message(cid, "No hay juego en este chat. Crea un nuevo juego con /newgame")
	except Exception as e:
		bot.send_message(cid, str(e))
		log.error("Unknown error: " + str(e))  

@restricted
def command_debug(update: Update, context: CallbackContext):
	bot = context.bot	
	# uid = update.message.from_user.id
	cid = update.message.chat_id
	game = get_game(cid)
	game.is_debugging = True if not game.is_debugging else False
	bot.send_message(cid, "Debug Mode: ON" if game.is_debugging else "Debug Mode: OFF")

@player
def command_whisper(update: Update, context: CallbackContext):
	bot = context.bot	
	uid = update.message.from_user.id
	cid = update.message.chat_id
	game = get_game(cid)
	args = context.args
	player = game.find_player(' '.join(args))
	requester = game.playerlist[uid]
	if player is None:
		bot.send_message(game.cid, "El jugador no esta en el partido, recuerda poner el nombre que aparece en el board")
		return
	if player.whispering and player.whispering is not requester.name:
		bot.send_message(game.cid, f"El jugador ya esta haciendo whisper con {player.whispering}")
	elif requester.whispering and requester.whispering is not player.name:
		bot.send_message(game.cid, f"Ya estás haciendo whisper con {requester.whispering} terminalo con /endwhisper")
	else:
		# Si el jugador no esta haciendo whispering con nadie asigno whisper a él
		requester.whispering = player.name
		player.whispering = requester.name
		whisper_message = f"Se ha creado el whisper entre {requester.whispering} y {player.whispering}.\n Para terminarlo hacer /endwhisper"
		game.history.append(whisper_message)
		bot.send_message(game.cid, whisper_message)

@player
def command_endwhisper(update: Update, context: CallbackContext):
	bot = context.bot	
	uid = update.message.from_user.id
	cid = update.message.chat_id
	game = get_game(cid)
	
	requester = game.playerlist[uid]
	if requester.whispering:
		player = game.find_player(requester.whispering)
		requester.whispering = None
		player.whispering = None
		bot.send_message(game.cid, f"Se ha terminado el whisper entre {requester.name} y {player.name}")
	else:
		bot.send_message(game.cid, "No estas haciendo actualmente whispering")

@player
def command_nominate(update: Update, context: CallbackContext):
	bot = context.bot	
	args = context.args
	cid = update.message.chat_id
	uid = update.message.from_user.id
	game = get_game(cid)
	data = ' '.join(args).split(";")
	if len(data) == 2:
		# Busco el jugador a acusar
		player_name = data[0].strip()
		defender = game.find_player(player_name)
		accuser = game.playerlist[uid]
		if accuser.dead :
			bot.send_message(cid, "Un jugador muerto no puede nominar")
			return
		if defender is None:
			bot.send_message(cid, "El jugador ingresado no existe")
			return
		if not game.board.state.can_nominate:
			bot.send_message(cid, "El storyteller no ha habilitado las nominaciones")
			return

		game.board.state.accuser = accuser
		game.board.state.defender = defender
		game.board.state.accusation = data[1].strip()
		message_nomination = f"De repente {player_call(accuser)} se levanta y señala con el dedo a {player_call(defender)} deberias ir a la horca!\nMotivo: {game.board.state.accusation}"
		game.history.append(message_nomination)
		save_game(cid, f"Se nomino a: {defender.name}", game)		
		bot.send_message(game.cid, message_nomination, ParseMode.MARKDOWN)
	else:
		bot.send_message(game.cid, "Debes ingresar /nominate [Nombre jugador en Board];Texto Acusación")

@player
def command_defend(update: Update, context: CallbackContext):
	bot = context.bot	
	args = context.args
	cid = update.message.chat_id
	game = get_game(cid)
	state = game.board.state
	uid = update.message.from_user.id
	if len(args) > 0:
		# Si el jugador que defiende no es el defensor...
		# log.info(state.defender.uid)
		# log.info(uid)
		if state.defender.uid != uid:
			bot.send_message(game.cid, f"El mensaje debe ser enviado por {player_call(state.defender)}")
		defender = state.defender
		accuser = state.accuser
		state.defense = " ".join(args)
		# Se da posibilidad que vote el primero
		state.clock = 0
		save_game(cid, "Defensa acusacion", game)
		bot.send_message(game.cid, f"Entonces {player_call(defender)} mira a los ojos a {player_call(accuser)} y dice a todo el pueblo: {state.defense}", ParseMode.MARKDOWN)
	else:
		bot.send_message(game.cid, "Debes ingresar algo para tu defensa")

@storyteller
def command_clear(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	game = get_game(cid)
	game.clear_nomination()
	bot.send_message(cid, "Se eliminó la acusación actual")
	save_game(cid, "Fix", game)

@storyteller
def command_toggle_nominations(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	game = get_game(cid)
	game.toggle_nominations()
	msg = "abierto" if game.board.state.can_nominate else "cerrado"
	bot.send_message(cid, f"Se han {msg} las nominaciones")
	save_game(cid, "Fix", game)
	
@storyteller
def command_set_player_order(update: Update, context: CallbackContext):
	bot = context.bot	
	args = context.args
	cid = update.message.chat_id
	game = get_game(cid)
	players = ' '.join(args)
	game.set_playerorder(players.split(","))
	save_game(cid, "Jugadores seteados", game)
	bot.send_message(game.cid, "Jugadores reorganizados")

@player
def command_tick(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	uid = update.message.from_user.id

	game = get_game(cid)
	if uid == game.storyteller or (game.get_current_voter() is not None and game.get_current_voter().uid == uid):
		clock_msg = game.advance_clock()
		bot.send_message(cid, clock_msg, ParseMode.MARKDOWN)	
		board_text = game.board.print_board(game)
		if game.board_message_id:
			bot.edit_message_text(board_text, cid, game.board_message_id, parse_mode=ParseMode.MARKDOWN)
		else:
			game.board_message_id = bot.send_message(cid, board_text, ParseMode.MARKDOWN)
		save_game(cid, "Cloak Advance", game)
	else:
		bot.send_message(cid, "No puedes hacer /tick porque no eres el storyteller ni el jugador que tiene que votar", ParseMode.MARKDOWN)

@player
def command_vote(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	uid = update.message.from_user.id
	game = get_game(cid)

	# if uid == game.storyteller and len(args) > 0:
	# Si el voto ya estaba no hago nada
	if uid in game.board.state.votes:
		return
	if game.can_modify_vote(uid):
		# Solo puede votar si esta vivo o si tiene el ultimo voto
		voter = game.playerlist[uid]
		if not voter.dead or (voter.dead and voter.has_last_vote):
			game.board.state.votes[uid] = "si"
			# Si el jugador esta muerto se le quita el ultimo voto
			if voter.dead:
				voter.has_last_vote = False
			save_game(cid, "Vote", game)
			board_text = game.board.print_board(game)
			if game.board_message_id:			
				bot.edit_message_text(board_text, cid, game.board_message_id, parse_mode=ParseMode.MARKDOWN)
			else:
				game.board_message_id = bot.send_message(cid, board_text, ParseMode.MARKDOWN)
			if game.get_current_voter().uid == uid:
				bot.send_message(cid, "Has votado, puedes pasar al proximo jugador con /tick", ParseMode.MARKDOWN)
		else:
			bot.send_message(cid, "No puedes votar ya que estas muerto y has gastado tu voto haz /tick", ParseMode.MARKDOWN)
	else:
		bot.send_message(cid, "No puedes modificar tu voto porque ha pasado tu turno", ParseMode.MARKDOWN)


@player
def command_refresh(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	uid = update.message.from_user.id
	game = get_game(cid)
	player = game.playerlist[uid]
	player.name = update.message.from_user.first_name.replace("_", " ")
	player.nick = update.message.from_user.username
	bot.send_message(cid, "Se ha modificado exitosamente al jugador", ParseMode.MARKDOWN)

@player
def command_info(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	uid = update.message.from_user.id
	game = get_game(cid)
	player = game.find_player_by_id(uid)
	
	if player is not None:
		bot.send_message(uid, f"""*Datos del jugador:*
Nombre: {player.name}
Nick: {player.nick}
Rol: {player.role}
Descripción del rol: {player.role_description}
Afiliation : {player.afiliation}
Tipo de personaje: {player.townfolk_Outsider_Minion_Demon}""", ParseMode.MARKDOWN)

@player
def command_clearvote(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	uid = update.message.from_user.id
	game = get_game(cid)

	if uid not in game.board.state.votes:
		return

	if game.can_modify_vote(uid):
		game.board.state.votes.pop(uid, None)
		voter = game.playerlist[uid]
		# Si el votante estaba muerto y le quite el ultimo voto, se lo devuelvo.
		if voter.dead:
			voter.has_last_vote = True
		save_game(cid, "Clear Vote", game)
		board_text = game.board.print_board(game)
		if game.board_message_id:			
			bot.edit_message_text(board_text, cid, game.board_message_id, parse_mode=ParseMode.MARKDOWN)
		else:
			game.board_message_id = bot.send_message(cid, board_text, ParseMode.MARKDOWN)
		if game.get_current_voter().uid == uid:
			bot.send_message(cid, "Has eliminado tu voto, puedes pasar al proximo jugador con /tick o votar con /vote", ParseMode.MARKDOWN)
	else:
		bot.send_message(cid, "*No puedes modificar tu voto porque ha pasado tu turno*", ParseMode.MARKDOWN)

@storyteller
def command_chopping(update: Update, context: CallbackContext):
	bot = context.bot	
	uid = update.message.from_user.id
	cid = update.message.chat_id
	game = get_game(cid)
	state = game.board.state

	if state.defender is not None:
		# Pone al defender en el chopping block
		state.chopping_block = state.defender
		state.chopping_block_votes = list(state.votes.values()).count("si")
		save_game(cid, "Chopping block", game)
	else:
		bot.send_message(cid, "No hay acusado para mandar al chopping block")
	# pone al defender actuan en el chopping block
	

@restricted
def command_fix(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	game = get_game(cid)
	state = game.board.state

	for player in game.playerlist.values():
		player.nick = ""
		player.role_description = ""

	bot.send_message(cid, "Fixed")
	save_game(cid, "Fix", game)

def save_game(cid, groupName, game):
	#Check if game is in DB first
	conn = psycopg2.connect(
		database=url.path[1:],
		user=url.username,
		password=url.password,
		host=url.hostname,
		port=url.port
	)
	cur = conn.cursor()			
	log.info("Searching Game in DB")
	query = "select * from games_blood where id = %s;"
	cur.execute(query, [cid])
	dbdata = cur.fetchone()
	if cur.rowcount > 0:
		log.info('Updating Game')
		gamejson = jsonpickle.encode(game)
		#query = "UPDATE games_blood SET groupName = %s, data = %s WHERE id = %s RETURNING data;"
		query = "UPDATE games_blood SET groupName = %s, data = %s WHERE id = %s;"
		cur.execute(query, (groupName, gamejson, cid))
		#log.info(cur.fetchone()[0])
		conn.commit()		
	else:
		log.info('Saving Game in DB')
		gamejson = jsonpickle.encode(game)
		query = "INSERT INTO games_blood(id , groupName, tipojuego , data) VALUES (%s, %s, %s, %s);"
		#query = "INSERT INTO games(id , groupName  , data) VALUES (%s, %s, %s) RETURNING data;"
		cur.execute(query, (cid, groupName, "blood", gamejson))
		#log.info(cur.fetchone()[0])
		conn.commit()
	conn.close()

def delete_game(cid):
	conn = psycopg2.connect(
		database=url.path[1:],
		user=url.username,
		password=url.password,
		host=url.hostname,
		port=url.port
	)
	cur = conn.cursor()
	#log.info("Deleting Game in DB")
	query = "DELETE FROM games_blood WHERE id = %s;"
	cur.execute(query, [cid])
	conn.commit()
	conn.close()
