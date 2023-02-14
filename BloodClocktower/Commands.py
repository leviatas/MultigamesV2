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
		bot = context.bot
		cid = update.message.chat_id		
		game = get_game(cid)

		if user_id != game.storyteller:
			update.effective_message.reply_text("No tienes acceso, ya que no eres el Storyteller")
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

def get_game(cid):
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
		#bot.send_message(cid, game.print_roles())
		conn.close()
		return game
	else:
		log.info("Game Not Found")
		conn.close()
		return None

def command_board(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	game = get_game(cid)
	if game.board:
		try:
			bot.send_message(cid, game.board.print_board(game), ParseMode.MARKDOWN)
		except Exception :
			game.board.print_board(bot, game)
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
		bot.send_message(game.cid, "Ya te has unido al juego, %s!" % fname)
	elif len(game.playerlist) >= 10:
		bot.send_message(game.cid, "Han llegado al maximo de jugadores. Por favor comiencen el juego con /startgame!")
	else:
		#uid = update.message.from_user.id
		player = Player(fname, uid)
		try:
			#Commented to dont disturb player during testing uncomment in production
			bot.send_message(uid, "Te has unido a un juego en %s. Pronto te dire cual es tu rol secreto." % groupName)
			# choose_posible_role(bot, cid, uid)

			game.add_player(uid, player)
			log.info("%s (%d) joined a game in %d" % (fname, uid, game.cid))
			if len(game.playerlist) > 4:
				bot.send_message(game.cid, fname + " se ha unido al juego. Escribe /startgame si este es el último jugador y quieren comenzar con %d jugadores!" % len(game.playerlist))
			elif len(game.playerlist) == 1:
				bot.send_message(game.cid, "%s se ha unido al juego. Hay %d jugador en el juego y se necesita 5-10 jugadores." % (fname, len(game.playerlist)))
			else:
				bot.send_message(game.cid, "%s se ha unido al juego. Hay %d jugadores en el juego y se necesita 5-10 jugadores" % (fname, len(game.playerlist)))
				# Luego dicto los jugadores que se han unido
			jugadoresActuales = "Los jugadores que se han unido al momento son:\n"
			for player in game.playerlist.items:
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

@storyteller
def command_firstnight(update: Update, context: CallbackContext):
	bot = context.bot	
	uid = update.message.from_user.id
	cid = update.message.chat_id
	game = get_game(cid)

	bot.send_message(game.cid, f"Comienza la primera noche, todos... cierren los ojos...")

@storyteller
def command_day(update: Update, context: CallbackContext):
	bot = context.bot	
	uid = update.message.from_user.id
	cid = update.message.chat_id
	game = get_game(cid)
	# Se incrementa el dia
	game.board.state.day += 1
	game.board.state.phase = "Día"
	bot.send_message(game.cid, f"Todos, abran los ojos...")

@storyteller
def command_night(update: Update, context: CallbackContext):
	bot = context.bot	
	uid = update.message.from_user.id
	cid = update.message.chat_id
	game = get_game(cid)
	game.board.state.phase = "Noche"
	bot.send_message(game.cid, f"Todos, cirren los ojos...")

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
		player.dead = True
		save_game(cid, f"Matamos a {player_name}", game)
		bot.send_message(game.cid, f"Jugador {player_name} te han matado, no posees más tu habilidad, pero puedes hablar y votar una última vez")
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
	args = context.args
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