from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.ext import (CallbackContext)
import GamesController

import jsonpickle
import os
import psycopg2
from psycopg2 import sql
import urllib.parse
import logging as log

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
		log.info("Game Found")
		jsdata = dbdata[2]
		#log.info("jsdata = %s" % (jsdata))				
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
		bot.send_message(cid, "There is no running game in this chat. Please start the game with /startgame")

def command_rules(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id	
	msg = """Reglas de Blood on the clocktower
	"""
	bot.send_message(cid, msg, ParseMode.MARKDOWN)