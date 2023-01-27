import json
import logging as log
import datetime
import os
import psycopg2
import urllib.parse
import sys
from time import sleep

import JustOne.Controller as JustOneController
import SayAnything.Controller as SayAnythingController
import Werewords.Controller as WerewordsController
import Unanimo.Controller as UnanimoController

from Utils import restricted, player_call, send_typing_action, get_game, delete_game, save, load_game, save_game
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update, ForceReply, Update
from telegram.ext import (CallbackContext)
import MainController
import GamesController

from Constants.Config import STATS
from Boardgamebox.Board import Board

from Boardgamebox.Game import Game
from SayAnything.Boardgamebox.Game import Game as GameSayAnything
from Arcana.Boardgamebox.Game import Game as GameArcana
from LostExpedition.Boardgamebox.Game import Game as GameLostExpedition
from Wavelength.Boardgamebox.Game import Game as GameWavelength
from Decrypt.Boardgamebox.Game import Game as GameDecrypt
from Werewords.Boardgamebox.Game import Game as GameWerewords
from Deception.Boardgamebox.Game import Game as GameDeception
from Unanimo.Boardgamebox.Game import Game as GameUnanimo

from Boardgamebox.Player import Player
from Boardgamebox.State import State
from Constants.Config import ADMIN
from collections import namedtuple

from PIL import Image
from io import BytesIO
from html2image import Html2Image

# Objetos que uso de prueba estaran en el state
from Constants.Cards import cartas_aventura
from Constants.Cards import opciones_opcional
from Constants.Cards import opciones_choose_posible_role
from Constants.Cards import modos_juego

from Constants.Config import JUEGOS_DISPONIBLES
from Constants.Config import MODULOS_DISPONIBES
from Constants.Config import HOJAS_AYUDA

from Constants.Cards import comandos
import random
import re
import requests
from bs4 import BeautifulSoup
# Objetos que uso de prueba estaran en el state

# Enable logging

log.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=log.INFO)
logger = log.getLogger(__name__)

#DB Connection I made a Haroku Postgres database first
urllib.parse.uses_netloc.append("postgres")
url = urllib.parse.urlparse(os.environ["DATABASE_URL"])


# Secret Moon
secret_moon_cid = '-1001206290323'

ALLOW_TEAM_COMMUNICATION = ['Decrypt']

def command_newgame_sql_command(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	cid, uid = update.message.chat_id, update.message.from_user.id
	if uid in ADMIN:
		try:
			#Check if game is in DB first
			conn = psycopg2.connect(
				database=url.path[1:],
				user=url.username,
				password=url.password,
				host=url.hostname,
				port=url.port
			)

			cursor = conn.cursor()			
			log.info("Executing in DB")
			#query = "select * from games;"
			query = " ".join(args)
			cursor.execute(query)
			#dbdata = cur.fetchone()
			if cursor.rowcount > 0:
				bot.send_message(cid, 'Resultado de la consulta:')
				for table in cursor.fetchall():
					#bot.send_message(cid, len(str(table)))
					tabla_str = str(table)
					# Si supera el maximo de caracteres lo parto
					max_length_msg = 3500
					if len(tabla_str) < max_length_msg:
						bot.send_message(cid, table)
					else:
						n = max_length_msg
						parts = [tabla_str[i:i+n] for i in range(0, len(tabla_str), n)]
						for part in parts:
							bot.send_message(cid, part)
			else:
				bot.send_message(cid, 'No se obtuvo nada de la consulta')
			conn.close()
		except Exception as e:
			bot.send_message(cid, 'No se ejecuto el comando debido a: '+str(e))
			conn.rollback()
			conn.close()

def save_comm(update: Update, context: CallbackContext):
	bot = context.bot
	try:		
		cid = update.message.chat_id	
		game = get_game(cid)
		gameType = game.tipo
		newGroupName = ''
		save_game(cid, game.groupName if newGroupName == '' else newGroupName , game, gameType )
		#bot.send_message(cid, 'Se grabo correctamente.')
		#log.info('Se grabo correctamente.')
	except Exception as e:
		bot.send_message(cid, 'Error al grabar '+str(e))


def load(update: Update, context: CallbackContext):
	bot = context.bot

	cid = update.message.chat_id
	game = load_game(cid)			
	if game:
		GamesController.games[cid] = game
		bot.send_message(cid, "Juego Cargado exitosamente")
		

	else:
		bot.send_message(cid, "No existe juego")		

def reload(update: Update, context: CallbackContext):
	bot = context.bot

	cid = update.message.chat_id
	game = get_game(cid)
	if game:
		bot.send_message(cid, "Juego Cargado exitosamente")
	else:
		bot.send_message(cid, "No existe juego")



	
def command_hoja_ayuda(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	uid = update.message.from_user.id
	game = get_game(cid)	
	help_text = HOJAS_AYUDA.get(game.tipo)	
	chat_send = cid if game.modo == 'Solitario' else uid
	bot.send_message(chat_send, help_text, ParseMode.MARKDOWN)
	if game.tipo == 'LostExpedition':
		bot.send_photo(chat_send, photo=open('/img/LostExpedition/Ayuda01.jpg', 'rb'))
		bot.send_photo(chat_send, photo=open('/img/LostExpedition/Ayuda02.jpg', 'rb'))

def command_info(update: Update, context: CallbackContext):
	bot = context.bot
	cid, uid, groupType = update.message.chat_id, update.message.from_user.id, update.message.chat.type
	
	if groupType not in ['group', 'supergroup']:
		# En caso de no estar en un grupo y en privado con el bot muestro todos los juegos donde esta el jugador.
		# Independeinte de si pide todos, tengo que obtenerlos a todos para preguntarle cualquier quiere tener info
		all_games_unfiltered = MainController.getGamesByTipo("Todos")	
		# Me improtan los juegos que; Este el jugador, hayan sido iniciados, datinivote no sea null y que cumpla reglas del tipo de juego en particular
		all_games = {key: "{}: {}".format(game.groupName, game.tipo) for key, game in all_games_unfiltered.items() if uid in game.playerlist and game.board != None }
		msg = "Elija el juego para obtener /info en privado"
		simple_choose_buttons(bot, cid, uid, uid, "chooseGameInfo", msg, all_games, False, 2)
	else:		
		game = get_game(cid)
		if game:
			if uid in game.playerlist:								
				player = game.playerlist[uid]
				bot.send_message(uid, player.get_private_info(game), ParseMode.MARKDOWN)				
			else:
				bot.send_message(cid, "Debes ser un jugador del partido para obtener informacion.")
		else:
			bot.send_message(cid, "No hay juego creado en este chat")

def callback_info(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_info called')
	callback = update.callback_query
	
	regex = re.search(r"(-?[0-9]*)\*chooseGameInfo\*(.*)\*(-?[0-9]*)", callback.data)
	opcion, uid = regex.group(2), int(regex.group(3))
	
	game = get_game(int(opcion))
	
	if uid in game.playerlist:								
		player = game.playerlist[uid]
		bot.send_message(uid, player.get_private_info(game), ParseMode.MARKDOWN)				
	else:
		bot.send_message(uid, "Debes ser un jugador del partido para obtener informacion.")
	
	
def command_showstats(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('command_showstats called')
	cid, uid = update.message.chat_id, update.message.from_user.id	
	if uid in ADMIN:
		game = get_game(cid)
		if not game:
			bot.send_message(cid, "No hay juego creado en este chat")
			return
		player = game.playerlist[uid]		
		bot.send_message(cid, player.print_stats())

def command_help(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	'''
	help_text = "Eventos amarillos son obligatorios\n" + \
	"Eventos rojo son obligatorios pero tenes que elegir 1\n"  + \
	"Eventos Azules son opcionales\n"
	'''
	help_text = "\nLos siguientes comandos estan disponibles:\n"
	help_text += commands	
	bot.send_message(cid, help_text)
		
def command_symbols(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	url_img = '/img/LostExpedition/Ayuda01.jpg'		
	bot.send_photo(cid, photo=url_img)
	url_img = '/img/LostExpedition/Ayuda02.jpg'
	bot.send_photo(cid, photo=url_img)

def command_reglas(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	texto_reglas = "Solitario: \n" + \
			"*Dia*: Obten 6 cartas. 2 mazo, 2 mano, 1 mazo, 1 mano.\n*Se ordenan por número.*\nResuelve.\n*Pierde 1 comida.*\n" + \
			"*Noche*: Primera de la mano. Poner de mazo o mano hasta completar 6.\n*Se puede poner adelante o atras en la ruta.*\nResuelve.\n*Pierde 1 comida.* Ir a día."			
	
	bot.send_message(cid, texto_reglas, ParseMode.MARKDOWN)

	
		
def command_prueba(update: Update, context: CallbackContext):
	bot = context.bot
	#log.info(update.message.from_user.id)
	#log.info(update.message.chat_id)
	cid, uid = update.message.chat_id, update.message.from_user.id
	
	if uid in ADMIN:
		game = get_game(cid)
		
		#bot.send_message(cid, "Este es el grupo ({0}) - Cuyo nombre es {1} y tipo es {2}".format(cid, groupName, groupType))
		#bot.send_message(cid, chat_data)
		#bot.send_message(cid, user_data)
		
		SayAnythingController.call_players_to_vote(bot, game)
		
		'''
		
		if not game:
			bot.send_message(cid, "No hay juego creado en este chat")
			return
		#bot.send_message(uid, "Respondeme", reply_markup=ForceReply())
		bot.send_message(uid, "/clue algo -312312312")
		'''

commands = """/newgame - Crea un nuevo juego
/delete - Borra juego actual
/claim - Guarda mensaje en historial
/history - Ver Historial
/myturn - Juego que requiere atención
/myturns - Todos los juegos que requieren atención
/call - Llama a los jugadores a actuar
/board - Muestra tablero de juego
/players - Muestra y llama a todos los jugadores
/info - Muestra la información personal al jugador
/help - Muestra comandos disponibles
/startgame - Inicia el juego
/join - Te une al partido en el grupo actual"""

symbols = [
    u"\u25FB\uFE0F" + ' Empty field without special power',
    u"\u2716\uFE0F" + ' Field covered with a card',  # X
    u"\U0001F52E" + ' Presidential Power: Policy Peek',  # crystal
    u"\U0001F50E" + ' Presidential Power: Investigate Loyalty',  # inspection glass
    u"\U0001F5E1" + ' Presidential Power: Execution',  # knife
    u"\U0001F454" + ' Presidential Power: Call Special Election',  # tie
    u"\U0001F54A" + ' Liberals win',  # dove
    u"\u2620" + ' Fascists win'  # skull
]

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
	
def command_start(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	bot.send_message(cid,"Bot para multiples juegos. Preguntar al ADMIN por los juegos disponibles")
    #command_help(bot, update)

def command_rules(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	game = get_game(cid)
	
	if game is None:
		bot.send_message(cid, "No hay ningun juego en este grupo:")
	else:
		rules = game.get_rules()
		if len(rules) > 1:
			btn = [[InlineKeyboardButton("Reglas", url=rules[0])]]
			rulesMarkup = InlineKeyboardMarkup(btn)
			bot.send_message(cid, rules[1], reply_markup=rulesMarkup)
		else:
			bot.send_message(cid, rules[0], ParseMode.MARKDOWN)

# prints statistics, only ADMIN
def command_stats(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	if cid == ADMIN:		
		bot.send_message(cid, "Estadisticas pronto...")
		
def command_cancelgame(update: Update, context: CallbackContext):
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

def command_votes(update: Update, context: CallbackContext):
	bot = context.bot
	try:
		#Send message of executing command   
		cid = update.message.chat_id
		#bot.send_message(cid, "Looking for history...")
		#Check if there is a current game 
		if cid in GamesController.games.keys():
			game = GamesController.games.get(cid, None)
			if not game.dateinitvote:
				# If date of init vote is null, then the voting didnt start          
				bot.send_message(cid, "The voting didn't start yet.")
			else:
				#If there is a time, compare it and send history of votes.
				start = game.dateinitvote
				stop = datetime.datetime.now()
				elapsed = stop - start
				if elapsed > datetime.timedelta(minutes=1):
					history_text = "Vote history for President %s and Chancellor %s:\n\n" % (game.board.state.nominated_president.name, game.board.state.nominated_chancellor.name)
					for player in game.player_sequence:
						# If the player is in the last_votes (He voted), mark him as he registered a vote
						if player.uid in game.board.state.last_votes:
							history_text += "%s ha dado pista.\n" % (game.playerlist[player.uid].name)
						else:
							history_text += "%s *no* ha dado pista.\n" % (game.playerlist[player.uid].name)
					bot.send_message(cid, history_text, ParseMode.MARKDOWN)
					
				else:
					bot.send_message(cid, "Five minutes must pass to see the votes") 
		else:
			bot.send_message(cid, "There is no game in this chat. Create a new game with /newgame")
	except Exception as e:
		bot.send_message(cid, str(e))

def command_call(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	import JustOne.Commands as JustoneCommands
	
	#Send message of executing command   
	cid = update.message.chat_id
	uid = update.effective_user.id
	#bot.send_message(cid, "Looking for history...")
	#Check if there is a current game 

	# Si soy yo y es mi privado hago call a todos.
	if cid == uid and uid == ADMIN[0]:
		# Call manual a todos los partidos
		filtro = 'Todos'
		if len(args) > 0:
			filtro = args[0]
		all_games = MainController.getGamesByTipo(filtro)
		log.info("Llamada a todos los juegos con call")
		bot.send_message(cid, "Realizando call a todas las apps.")
		for game_chat_id, game in all_games.items():
			log.info("Llamada a todos los juegos con call")
			if getattr(game, "call", None):
				# Si game tiene atributo call lo utilizo
				try:
					game.call(context)
				except Exception as e:
					bot.send_message(cid, "Chat {} Usuario {} Error:\n{}".format(game_chat_id, game.tipo, str(e)))
				
		return
	
	
	game = get_game(cid)
	#log.info(game.tipo)
	
	if game:
		if getattr(game, "call", None):
			log.info("Se llamo por el medio del game")
			# Si game tiene atributo call lo utilizo
			game.call(context)
		else:
			bot.send_message(cid, "El juego no tiene el metodo /call")
	else:
		bot.send_message(cid, "There is no game in this chat. Create a new game with /newgame")
		
def command_showhistory(update: Update, context: CallbackContext):
	bot = context.bot
	#game.pedrote = 3
	try:
		#Send message of executing command   
		cid = update.message.chat_id
		#Check if there is a current game 
		game = get_game(cid)
		if game:			
			#bot.send_message(cid, "Current round: " + str(game.board.state.currentround + 1))
			uid = update.message.from_user.id
			for history in game.getHistory(uid):
				if len(history) > 0:
					bot.send_message(uid, history, ParseMode.MARKDOWN)
		else:
			bot.send_message(cid, "No hay ninguna partida en este chat.")
	except Exception as e:
		bot.send_message(cid, str(e))
		log.error("Unknown error: " + str(e))  
		
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
			if uid in game.playerlist:								
				if len(args) > 0:
					#Data is being claimed
					claimtext = ' '.join(args)
					claimtexttohistory = "El jugador %s declara: %s" % (game.playerlist[uid].name, claimtext)
					bot.send_message(cid, "Tu declaración: %s fue agregada al historial." % (claimtext))
					game.history.append("%s" % (claimtexttohistory))
				else:					
					bot.send_message(cid, "Debes mandar un mensaje para hacer una declaración.")

			else:
				bot.send_message(cid, "Debes ser un jugador del partido para declarar algo.")				
		else:
			bot.send_message(cid, "No hay juego en este chat. Crea un nuevo juego con /newgame")
	except Exception as e:
		bot.send_message(cid, str(e))
		log.error("Unknown error: " + str(e))    
		

	
def command_choose_posible_role(update: Update, context: CallbackContext):
	bot = context.bot
	cid, uid = update.message.chat_id, update.message.from_user.id
	choose_posible_role(bot, cid, uid)
def choose_posible_role(bot, cid, uid):
	frase_regex = "chooserole"
	pregunta_arriba_botones = "¿Qué rol quisieras ser?"
	chat_donde_se_pregunta = uid
	multipurpose_choose_buttons(bot, cid, uid, chat_donde_se_pregunta, frase_regex, pregunta_arriba_botones, opciones_choose_posible_role)
def callback_choose_posible_role(update: Update, context: CallbackContext):
	bot = context.bot
	callback = update.callback_query
	log.info('callback_choose_posible_role called: %s' % callback.data)	
	regex = re.search(r"(-[0-9]*)\*chooserole\*(.*)\*([0-9]*)", callback.data)
	cid, opcion, uid = int(regex.group(1)), regex.group(2), int(regex.group(3))
	bot.edit_message_text("Mensaje Editado: Has elegido el Rol: %s" % opcion, cid, callback.message.message_id)
	bot.send_message(cid, "Ventana Juego: Has elegido el Rol %s" % opcion)
	bot.send_message(uid, "Ventana Usuario: Has elegido el Rol %s" % opcion)	


def multipurpose_choose_buttons(bot, cid, uid, chat_donde_se_pregunta, comando_callback, mensaje_pregunta, opciones_botones, one_line = True, items_each_line = 3):
	#sleep(3)
	btns = []
	# Creo los botones para elegir al usuario
	if one_line:	
		for opcion in opciones_botones:
			txtBoton = ""
			comando_op = opciones_botones[opcion]								
			for comando in comando_op["comandos"]:
				txtBoton += comando_op["comandos"][comando] + " "			
			txtBoton = txtBoton[:-1]
			datos = str(cid) + "*" + comando_callback + "*" + str(opcion) + "*" + str(uid)
			if "restriccion" in comando_op:
				if comando_op["restriccion"] == "admin" and uid in ADMIN:
					btns.append([InlineKeyboardButton(txtBoton, callback_data=datos)])
			else:
				btns.append([InlineKeyboardButton(txtBoton, callback_data=datos)])
	else:
		btn_group = []
		for opcion in opciones_botones:
			txtBoton = ""
			comando_op = opciones_botones[opcion]								
			for comando in comando_op["comandos"]:
				txtBoton += comando_op["comandos"][comando] + " "			
			txtBoton = txtBoton[:-1]
			datos = str(cid) + "*" + comando_callback + "*" + str(opcion) + "*" + str(uid)
			if "restriccion" in comando_op:
				if comando_op["restriccion"] == "admin" and uid in ADMIN:
					btn_group.append(InlineKeyboardButton(txtBoton, callback_data=datos))
			else:
				btn_group.append(InlineKeyboardButton(txtBoton, callback_data=datos))
			if len(btn_group) == items_each_line:				
				btns.append(btn_group)
				btn_group = []
		# Al finalizar si me quedo un grupo que no agregue con items, lo agrego.
		if len(btn_group) > 0:
			btns.append(btn_group)
	btnMarkup = InlineKeyboardMarkup(btns)
	#for uid in game.playerlist:
	bot.send_message(chat_donde_se_pregunta, mensaje_pregunta, reply_markup=btnMarkup)

# Comando para elegir el juego
#Se crea metodo general para crear jeugos
def command_newgame(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	uid = update.message.from_user.id
	try:
		game = GamesController.games.get(cid, None)
		groupType = update.message.chat.type
		if groupType not in ['group', 'supergroup']:
			bot.send_message(cid, "Tienes que agregarme a un grupo primero y escribir /newgame allá!")
		elif game:
			bot.send_message(cid, "Hay un juego comenzado en este chat. Si quieres terminarlo escribe /delete!")
		else:			
			# Busco si hay un juego ya creado
			game = get_game(cid)
			if game:
				bot.send_message(cid, "Hay un juego ya creado, borralo con /delete o unite con /join")
			else:
								
				bot.send_message(cid, "Comenzamos eligiendo el juego a jugar")
				configurarpartida(bot, cid, uid)
	except Exception as e:
		bot.send_message(cid, str(e))

def command_configurar_partida(update: Update, context: CallbackContext):
	bot = context.bot
	cid, uid = update.message.chat_id, update.message.from_user.id
	configurarpartida(bot, cid, uid)
		
def configurarpartida(bot, cid, uid):
	frase_regex = "choosegame"
	pregunta_arriba_botones = "¿Qué juego quieres jugar?"
	chat_donde_se_pregunta = cid
	multipurpose_choose_buttons(bot, cid, uid, chat_donde_se_pregunta, frase_regex, pregunta_arriba_botones, JUEGOS_DISPONIBLES, False, 2)
	
def callback_choose_game(update: Update, context: CallbackContext):
	bot = context.bot
	callback = update.callback_query
	log.info('callback_choose_game called: %s' % callback.data)	
	regex = re.search(r"(-[0-9]*)\*choosegame\*(.*)\*([0-9]*)", callback.data)
	cid, opcion, uid, = int(regex.group(1)), regex.group(2), int(regex.group(3))
	bot.edit_message_text("Has elegido el juego: %s" % opcion, cid, callback.message.message_id)
	
	# Inicio el juego con los valores iniciales, el chat en que se va a jugar, el iniciador y el nombre del chat
	groupName = update.effective_chat.title
	
	game = CreateGame(cid, uid, opcion, groupName, bot)
	
	modulos_disponibles_juego = MODULOS_DISPONIBES[opcion]
	
	# Si hay solo un modo de juego, lo pongo. Sino pregunto cual se quiere jugar
	if len(modulos_disponibles_juego) == 1:	
		game.modo = next(iter(modulos_disponibles_juego))
		bot.send_message(cid, "Solo hay un modulo y se pone ese %s" % game.modo)
		bot.send_message(cid, "Cada jugador puede unirse al juego con el comando /join.\nEl iniciador del juego (o el administrador) pueden unirse tambien y escribir /startgame cuando todos se hayan unido al juego!")
		save_game(cid, groupName, game, game.tipo)
		#save(bot, game.cid)
	else:
		frase_regex = "choosemode"
		pregunta_arriba_botones = "¿Qué modo de juego quieres jugar?"
		chat_donde_se_pregunta = cid
		multipurpose_choose_buttons(bot, cid, uid, chat_donde_se_pregunta, frase_regex, pregunta_arriba_botones, modulos_disponibles_juego)


def CreateGame(cid, uid, tipo, groupName, bot):
	# Al momento solo SayAnything y Arcana tienen game custom
	if tipo == 'SayAnything':
		GamesController.games[cid] = GameSayAnything(cid, uid, groupName, tipo)	
	elif tipo == 'Arcana':
		GamesController.games[cid] = GameArcana(cid, uid, groupName, tipo)
	elif tipo == 'Wavelength':
		GamesController.games[cid] = GameWavelength(cid, uid, groupName, tipo)
	elif tipo == 'LostExpedition':
		GamesController.games[cid] = GameLostExpedition(cid, uid, groupName, tipo)
	elif tipo == 'Decrypt':
		GamesController.games[cid] = GameDecrypt(cid, uid, groupName, tipo)	
	elif tipo == 'Werewords':
		GamesController.games[cid] = GameWerewords(cid, uid, groupName, tipo)
		bot.send_message(cid, "Comenzamos eligiendo los modulos a incluir en tu partida de Werewords")
		#WerewordsController.configurar_partida(bot, GamesController.games[cid])
	elif tipo == 'Deception':
		GamesController.games[cid] = GameDeception(cid, uid, groupName, tipo)
	elif tipo == 'Unanimo':
		GamesController.games[cid] = GameUnanimo(cid, uid, groupName, tipo)
	else:
		GamesController.games[cid] = Game(cid, uid, groupName, tipo)

	return GamesController.games[cid]

def callback_choose_mode(update: Update, context: CallbackContext):
	bot = context.bot
	callback = update.callback_query
	log.info('callback_choose_mode called: %s' % callback.data)	
	regex = re.search(r"(-[0-9]*)\*choosemode\*(.*)\*([0-9]*)", callback.data)
	cid, opcion = int(regex.group(1)), regex.group(2)
	bot.edit_message_text("Has elegido el modo: %s" % opcion, cid, callback.message.message_id)
	game = get_game(cid)
	game.modo = opcion
	bot.send_message(cid, "Cada jugador puede unirse al juego con el comando /join.\nEl iniciador del juego (o el administrador) pueden unirse tambien y escribir /startgame cuando todos se hayan unido al juego!")
	save(bot, game.cid)
	
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
		if uid == ADMIN:
			for i,k in zip(args[0::2], args[1::2]):
				fname = i.replace("_", " ")
				uid = int(k)
				player = Player(fname, uid)
				game.add_player(uid, player)
				log.info("%s (%d) joined a game in %d" % (fname, uid, game.cid))
				save(cid, "Game in join state", game)
	
	if groupType not in ['group', 'supergroup']:
		bot.send_message(cid, "Tienes que agregarme a un grupo primero y escribir /newgame allá!")
	elif not game:
		bot.send_message(cid, "No hay juego en este chat. Crea un nuevo juego con /newgame")
	elif game.board and not "permitir_ingreso_tardio" in JUEGOS_DISPONIBLES[game.tipo]:
		# Si el juego se ha comenzado, y no permite ingreso tardio...
		bot.send_message(cid, "El juego ha comenzado. Por favor espera el proximo juego!")
	elif uid in game.playerlist:
		bot.send_message(game.cid, "Ya te has unido al juego, %s!" % fname)
	else:
		#uid = update.message.from_user.id
		try:
			max_jugadores = MODULOS_DISPONIBES[game.tipo][game.modo]["max_jugadores"]
			min_jugadores = MODULOS_DISPONIBES[game.tipo][game.modo]["min_jugadores"]
			
			# Si se ha alcanzado el maximo de jugadores no te puedes unir.
			if len(game.playerlist) == max_jugadores:
				bot.send_message(game.cid, "Se ha alcanzado previamente el maximo de jugadores. Espera el proximo juego!")
			else:
				# Uno al jugador a la partida
				if game.is_debugging:
					bot.send_message(ADMIN[0], "Se has unido a un juego en %s." % groupName)
				else:
					bot.send_message(uid, "Te has unido a un juego en %s." % groupName)
				
				game.add_player(uid, fname)

				# Al unirse a partidas para que se ingrese en la BD los agrego.
				MainController.add_user(uid, fname)
				MainController.add_member_group(cid, uid)
				log.info("%s (%d) joined a game in %s (%d) of type %s" % (fname, uid, groupName, game.cid, game.tipo))
				
				# Si es un ingreso tardio ingreso al jugador en la player secuence
				if game.board:
					game.player_sequence.append(game.playerlist[uid])
				
				# Si se ha alcanzado el minimo o superado, y no esta ya empezado
				if len(game.playerlist) == max_jugadores and not game.board:
					command_startgame(bot, update)
				elif len(game.playerlist) >= min_jugadores:
					if game.board:
						bot.send_message(game.cid, fname + " se ha unido al juego. Hay %s/%s jugadores." % (str(len(game.playerlist)), max_jugadores))
					else:
						bot.send_message(game.cid, fname + " se ha unido al juego. Hay %s/%s jugadores.\nPueden poner /startgame para comenzar" % (str(len(game.playerlist)), max_jugadores))
				else:
					bot.send_message(game.cid, fname + " se ha unido al juego. Todavia no se ha llegado al minimo de jugadores. Faltan: %s " % (str(min_jugadores - len(game.playerlist))))
				
				save(bot, game.cid)
					
		except Exception as e:
			bot.send_message(game.cid,
				fname + ", no puedo mandarte mensajes privados o hubo un error. Por favor anda a @MultiGamesByLevibot y hace click en \"Start\".\nLuego tiene que hacer /join de nuevo." + str(e))

def command_startgame(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('command_startgame called')
	cid = update.message.chat_id
	game = get_game(cid)
	if not game:
		bot.send_message(cid, "There is no game in this chat. Create a new game with /newgame")
	#elif game.board:
	#	bot.send_message(cid, "The game is already running!")
	elif update.message.from_user.id not in ADMIN and update.message.from_user.id != game.initiator and bot.getChatMember(cid, update.message.from_user.id).status not in ("administrator", "creator"):
		bot.send_message(game.cid, "Solo el creador del juego o un admin puede iniciar con /startgame")	
	elif game.board:
		bot.send_message(cid, "El juego ya empezo!")
		
	else:
		
		# Verifico si la configuracion ha terminado y se han unido los jugadores necesarios		
		min_jugadores = MODULOS_DISPONIBES[game.tipo][game.modo]["min_jugadores"]
		
		if len(game.playerlist) >= min_jugadores:
			save(bot, game.cid)
			MainController.init_game(bot, game)
		else:
			bot.send_message(game.cid, "Falta el numero mínimo de jugadores. Faltan: %s " % (str(min_jugadores - len(game.playerlist))))
			
def command_roll(update: Update, context: CallbackContext):
	bot = context.bot
	import GameCommands.SistemaD100Commands as SistemaD100Commands
	import GameCommands.HarryPotterCommands as HarryPotterCommands

	cid = update.message.chat_id
	uid = update.message.from_user.id
	# Me fijo si hay una partida, sino por defecto es D100
	game = get_game(cid)
	if game and uid in game.playerlist:
		#bot.send_message(cid, "*Juego encontrado*", ParseMode.MARKDOWN)
		if game.tipo == "SistemaD100":
			SistemaD100Commands.command_roll(update, context)
		elif game.tipo == "HarryPotter":
			HarryPotterCommands.command_roll(update, context)
		else:
			bot.send_message(cid, "*El juego no tiene commando roll*", ParseMode.MARKDOWN)
	else:
		SistemaD100Commands.command_roll(update, context)

def simple_choose_buttons(bot, cid, uid, chat_donde_se_pregunta, comando_callback, mensaje_pregunta, opciones_botones, one_line = True, items_each_line = 3):
	
	#sleep(3)
	btns = []
	# Creo los botones para elegir al usuario
	if one_line:
		for key, value in opciones_botones.items():
			txtBoton = value
			datos = str(cid) + "*" + comando_callback + "*" + str(key) + "*" + str(uid)
			#log.info(datos)
			#if comando_callback == "announce":
			#	bot.send_message(ADMIN[0], datos)
			btns.append([InlineKeyboardButton(txtBoton, callback_data=datos)])
	else:
		btn_group = []
		for key, value in opciones_botones.items():
			txtBoton = value
			datos = str(cid) + "*" + comando_callback + "*" + str(key) + "*" + str(uid)
			
			#if comando_callback == "announce":
			#	bot.send_message(ADMIN[0], datos)
			btn_group.append(InlineKeyboardButton(txtBoton, callback_data=datos))
			if len(btn_group) == items_each_line:				
				btns.append(btn_group)
				btn_group = []
		# Si no completa en multiplo de items_each_line agrego los que faltan.
		if len(btn_group) > 0:
			btns.append(btn_group)
	btnMarkup = InlineKeyboardMarkup(btns)

	try:	
		#for uid in game.playerlist:
		game = get_game(cid)
		if game is not None and game.is_debugging:
			chat_donde_se_pregunta = ADMIN[0]
		bot.send_message(chat_donde_se_pregunta, mensaje_pregunta, reply_markup=btnMarkup, parse_mode=ParseMode.MARKDOWN)
		GamesController.simple_choose_buttons_retry = False
	except Exception as e:
		# Si tira error y estoy debugeando intento mandar de nuevo pero si no intente anteriormente
		game = get_game(cid)
		if game is not None and game.is_debugging and not GamesController.simple_choose_buttons_retry:
			GamesController.simple_choose_buttons_retry = True
			simple_choose_buttons(bot, cid, ADMIN[0], ADMIN[0], comando_callback, mensaje_pregunta, opciones_botones, one_line, items_each_line)
		else:
			bot.send_message(ADMIN[0], 'Error en simple_choose_buttons {}'.format(e))


	
	
def command_continue(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	import JustOne.Commands as JustoneCommands
	import LostExpedition.Commands as LostExpeditionCommands
	
	log.info('command_continue called')
	
	try:
		cid, uid = update.effective_chat.id, update.effective_user.id
	except Exception:
		cid, uid = args[1], args[2]
	
	game = load_game(cid)
	if game:
		GamesController.games[cid] = game		
		if game.tipo == 'LostExpedition':
			LostExpeditionCommands.command_continue(bot, game, uid)
		elif game.tipo == 'JustOne':
			log.info('continue Just One Game called')
			JustoneCommands.command_continue(bot, game, uid)
		else:
			bot.send_message(cid, "El juego no tiene comando continue")
	else:
		bot.send_message(cid, "No hay juego que continuar")
	
def command_jugadores(update: Update, context: CallbackContext):
	bot = context.bot	
	uid = update.message.from_user.id
	cid = update.message.chat_id
	
	game = get_game(cid)
	
	
	if not game:
		return
	
		
	jugadoresActuales = "Los jugadores que se han unido al momento son:\n"
	
	for uid in game.playerlist:
		jugadoresActuales += "{}\n".format(player_call(game.playerlist[uid]))
					
	bot.send_message(game.cid, jugadoresActuales, ParseMode.MARKDOWN)

@restricted	
def command_announce(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	uid = update.message.from_user.id
	cid = update.message.chat_id
	# Lo pongo estatico ya que no anunciare en todos los tipos de juegos.
	opciones_botones = { 
		"Unanimo" : "Unanimo",
		"Deception" : "Deception",
		"Werewords" : "Werewords", 
		"JustOne" : "Just One", 
		"Arcana" : "Arcana", 
		"Todos" : "Todos", 
		"Cancel" : "Cancel" }
	if len(args) < 1:
		bot.send_message(cid, "Edu, tenes que poner un mensaje", ParseMode.MARKDOWN)
		return
	GamesController.announce_text = ' '.join(args)
	simple_choose_buttons(bot, cid, 1234, uid, "announce", "En que juegos queres anunciar", opciones_botones)

# Comando para que el bot nos recuerde los partidos que tenemos 	
@send_typing_action
def command_myturn(update: Update, context: CallbackContext):
	bot = context.bot
	uid = update.message.from_user.id
	
	# Independeinte de si pide todos, tengo que obtenerlos a todos para saber cual es el de menos tiempo.
	all_games_unfiltered = MainController.getGamesByTipo("Todos")	
	# Me improtan los juegos que; Este el jugador, hayan sido iniciados, datinivote no sea null y que cumpla reglas del tipo de juego en particular
	all_games = {key:game for key, game in all_games_unfiltered.items() if uid in game.playerlist and game.board != None and verify_my_turn(game, uid) }
	
	# Le recuerdo solo el juego que mas tiempo lo viene esperando		
	#chat_id = min(all_games, key=lambda key: all_games[key].dateinitvote)
	try:
		chat_id = min(all_games, key=lambda key: datetime.datetime.now() if all_games[key].dateinitvote == None else all_games[key].dateinitvote)
		game_pendiente = all_games[chat_id]
		bot.send_message(uid, myturn_message(bot, game_pendiente , uid), ParseMode.MARKDOWN)
	except Exception:
		bot.send_message(uid, "*NO* tienes partidos pendientes", ParseMode.MARKDOWN)
		#ot.send_message(ADMIN[0], str(e))

@send_typing_action
def command_myturns(update: Update, context: CallbackContext):
	bot = context.bot
	uid = update.message.from_user.id
	
	# Independeinte de si pide todos, tengo que obtenerlos a todos para saber cual es el de menos tiempo.
	all_games_unfiltered = MainController.getGamesByTipo("Todos")	
	# Me improtan los juegos que; Este el jugador, hayan sido iniciados, datinivote no sea null y que cumpla reglas del tipo de juego en particular
	all_games = {key:game for key, game in all_games_unfiltered.items() if uid in game.playerlist and game.board != None and verify_my_turn(game, uid) }
	for game in all_games.values():		
		bot.send_message(uid, myturn_message(bot, game, uid), ParseMode.MARKDOWN)			
	if len(all_games) == 0:
		bot.send_message(uid, "*NO* tienes partidos pendientes", ParseMode.MARKDOWN)


@restricted
def command_set_config_data(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	cid = update.message.chat_id
	game = get_game(cid)
	try:
		game.configs[args[0]] = args[1]
	except Exception:
		# Si hay excepcion es que configs no existe
		game.configs = {}
		game.configs[args[0]] = args[1]
		bot.send_message()
		log.info('command_set_config_data successfull: {}{}'.format(args[0], args[1]))
	bot.send_message(cid, "La key {} y variable {} han sido agregadas al juego".format(args[0], args[1]))
	save(bot, cid)

# TODO Poner estos metodos en helpers o usar los de cada juego en particular en su controller
def verify_my_turn(game, uid):
	import SayAnything.Commands as SayAnythingCommands
	
	if game.tipo == 'JustOne' or game.tipo == 'SayAnything':
		if game.tipo == 'JustOne' and game.board.state.fase_actual == "Proponiendo Pistas":
			return uid not in game.board.state.last_votes and uid != game.board.state.active_player.uid
		if game.tipo == 'SayAnything' and game.board.state.fase_actual == "Proponiendo Pistas":
			voto_jugador = next((x for x in game.board.state.ordered_votes if x.player.uid == uid), None)
			return (not voto_jugador) and uid != game.board.state.active_player.uid		
		elif game.board.state.fase_actual == "Revisando Pistas":
			return game.board.state.reviewer_player.uid == uid
		elif game.board.state.fase_actual == "Adivinando":
			return game.board.state.active_player.uid == uid
		elif game.board.state.fase_actual == "Votando Frases":
			return SayAnythingCommands.verify_missing_votes_user(game, uid)	
	elif hasattr(game, 'verify_turn'):
		return game.verify_turn(uid)
		
		
	return False

def myturn_message(bot, game, uid):
	try:
		if game.tipo == 'JustOne':
			return JustOneController.myturn_message(game, uid)		
		elif game.tipo == 'SayAnything':
			#log.info("Fase: {} Grupo {}".format(game.board.state.fase_actual, game.groupName))
			if game.board.state.fase_actual == "Votando Frases":				
				SayAnythingController.send_vote_buttons(bot, game, uid)
				return "Te faltan votos"							
			log.info(game.groupName)
			return SayAnythingController.myturn_message(game, uid)	
		elif hasattr(game, 'myturn_message'):
			return game.myturn_message(uid)
	except Exception as e:
		return str(e)


def get_config_data(game, config_name):
	# Si por algun motivo tira excepcion siempre se devuelve None
	try:
		
		return game.configs.get(config_name, None)				
	except Exception :
		return None

def command_guess(update: Update, context: CallbackContext):
	bot = context.bot
	import JustOne.Commands as JustoneCommands
	import SayAnything.Commands as SayAnythingCommands
	import Arcana.Commands as ArcanaCommands

	cid = update.message.chat_id
	uid = update.message.from_user.id
	# Me fijo si hay una partida, sino por defecto es D100
	game = get_game(cid)
	if game and uid in game.playerlist:
		#bot.send_message(cid, "*Juego encontrado*", ParseMode.MARKDOWN)
		if game.tipo == "JustOne":
			JustoneCommands.command_guess(update, context)
		elif game.tipo == "Arcana":
			ArcanaCommands.command_guess(update, context)
		else:
			bot.send_message(cid, "*El juego no tiene commando guess*", ParseMode.MARKDOWN)
	else:
		bot.send_message(cid, "*No estas en ninguna partida en la que puedas hacer guess*", ParseMode.MARKDOWN)

def command_pass(update: Update, context: CallbackContext):
	bot = context.bot	
	import JustOne.Commands as JustoneCommands
	import SayAnything.Commands as SayAnythingCommands
	import Arcana.Commands as ArcanaCommands
	import Wavelength.Commands as WavelengthCommands

	cid = update.message.chat_id
	uid = update.message.from_user.id
	# Me fijo si hay una partida, sino por defecto es D100
	game = get_game(cid)
	if game and uid in game.playerlist:
		log.info(game.tipo)
		#bot.send_message(cid, "*Juego encontrado*", ParseMode.MARKDOWN)
		if game.tipo == "JustOne":
			JustoneCommands.command_pass(update, context)
		elif game.tipo == "Arcana":
			ArcanaCommands.command_pass(update, context)
		elif game.tipo == "Wavelength":
			WavelengthCommands.command_pass(update, context)
		else:
			bot.send_message(cid, "*El juego no tiene commando pass*", ParseMode.MARKDOWN)
	else:
		bot.send_message(cid, "*No estas en ninguna partida en la que puedas hacer pass*", ParseMode.MARKDOWN)

@restricted
def command_changestate(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	cid = update.message.chat_id
	try:
		game = get_game(cid)
		nuevo_estado = " ".join(args)
		game.board.state.fase_actual = nuevo_estado
		bot.send_message(cid, "Estado modificado a *{}*".format(nuevo_estado), ParseMode.MARKDOWN)
	except Exception as e:
		bot.send_message(cid, "Fallo modificar estado por *{}*".format(e), ParseMode.MARKDOWN)


def command_team(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	user_data = context.user_data
	# Busco los juegos en que este el player
	uid = update.message.from_user.id
	cid = update.message.chat_id

	if update.message.chat.type in ['group', 'supergroup']:
		bot.delete_message(cid, update.message.message_id)
		return

	if len(args) > 0:
		
		# Obtengo todos los juegos que tengan habilitada la comunicacion de equipos.
		games_tipo = {}
		for type_game in ALLOW_TEAM_COMMUNICATION:
			games_tipo.update(MainController.getGamesByTipo(type_game))
		
		btns, cid = get_choose_game_buttons(games_tipo, uid, callback_command = 'choosegameCHAT')
		user_data[uid] = ' '.join(args)			
		if len(btns) != 0:
			if len(btns) == 1:
				#Si es solo 1 juego lo hago automatico
				game = get_game(cid)
				bot.send_message(uid, "Se ha elegido automaticamente *{}*".format(game.groupName), ParseMode.MARKDOWN)
				
				for team in game.board.state.teams:
					if team.belongs(uid):
						player = team.getPlayer(uid)
						team.communicate_team(bot, user_data[uid], exclude = [], messanger = player.name, groupName = game.groupName)
			else:
				txtBoton = "Cancel"
				datos = "-1*choosegameCHAT*" + "prop" + "*" + str(uid)
				btns.append([InlineKeyboardButton(txtBoton, callback_data=datos)])
				btnMarkup = InlineKeyboardMarkup(btns)
				bot.send_message(uid, "En cual de estos grupos queres mandar el mensaje?", reply_markup=btnMarkup)
		else:
			mensaje_error = "No hay partidas en las que puedas hacer /team"
			bot.send_message(uid, mensaje_error)

def get_choose_game_buttons(games_tipo, uid, callback_command):	
	btns = []
	cid = None
	for game_chat_id, game in games_tipo.items():
		if uid in game.playerlist and game.board != None:
			log.info('TEAM CHAT uid: {}. Grupo: {}'.format(uid, game.groupName))			
			# Solo si el juego tiene equipos lo permito.
			if hasattr(game.board.state, 'teams'):
				# Pongo en cid el id del juego actual, para el caso de que haya solo 1
				cid = game_chat_id
				clue_text = "msg"
				# Creo el boton el cual eligirá el jugador
				txtBoton = game.groupName
				datos = str(game_chat_id) + "*" + callback_command + "*" + clue_text + "*" + str(uid)
				btns.append([InlineKeyboardButton(txtBoton, callback_data=datos)])
	return btns, cid
	
def callback_choose_game_chat(update: Update, context: CallbackContext):
	bot = context.bot
	user_data = context.user_data
	callback = update.callback_query
	log.info('callback_choose_game_prop called: %s' % callback.data)	
	regex = re.search(r"(-[0-9]*)\*choosegameCHAT\*(.*)\*([0-9]*)", callback.data)
	cid, uid = int(regex.group(1)), int(regex.group(3))
	
	if cid == -1:
		bot.edit_message_text("Cancelado", uid, callback.message.message_id)
		return	
	game = get_game(cid)
	mensaje_edit = "Has elegido el grupo {0}".format(game.groupName)	
	bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)	
	message = user_data[uid]	
	# Obtengo el juego y mando el mensaje a los compañeros
	for team in game.board.state.teams:
		if team.belongs(uid):
			player = team.getPlayer(uid)
			team.communicate_team(bot, message, exclude = [], messanger = player.name, groupName = game.groupName)

def command_toggle_debugging(update: Update, context: CallbackContext):
	bot = context.bot
	uid = update.message.from_user.id
	if uid in ADMIN:
		cid = update.message.chat_id
		game = get_game(cid)
		# Informo que el modo de debugging ha cambiado
		# Seteo si no la tiene inicializada.
		if not hasattr(game, "is_debugging"):
			game.is_debugging = False
		game.is_debugging = True if not game.is_debugging else False
		bot.send_message(cid, "Debug Mode: ON" if game.is_debugging else "Debug Mode: OFF")

def call_players_group(update: Update, context: CallbackContext):
	bot = context.bot
	# Llama a los jugadores que estan en el grupo.
	log.info('call_player_group called')
	cid = update.message.chat_id
	call_text = "Despierten!: "
	try:
		#Check if game is in DB first
		conn = psycopg2.connect(
				database=url.path[1:],
				user=url.username,
				password=url.password,
				host=url.hostname,
				port=url.port
			)
		cursor = conn.cursor()			
		#log.info("Searching Game in DB")
		query = "select * from users INNER JOIN users_group ON users.id = users_group.user_id where users_group.group_id = %s;"
		cursor.execute(query, [cid])
		
		if cursor.rowcount > 0:
			for table in cursor.fetchall():
				if bool(table[5]):
					call_text += "{} ".format(player_call(Player(table[1], int(table[4]) ) ))
				#if bool(table[5]) El 5 tiene true o false
				#table[1]
				#table[4]
				#table[5]
				#do = "stuff"
			bot.send_message(cid, call_text, ParseMode.MARKDOWN)
					
	except Exception as e:
		log.info('No se busco bien los jugadores debido al siguiente error: '+str(e))
		conn.rollback()

def callback_timer(update: Update, context: CallbackContext):
	cid = update.message.chat_id
	bot = context.bot
	job_queue = context.job_queue
	args = context.args
	game = get_game(cid)
	# Si existe el juego verifico que tenga comando sino se usa el uso pensado del timer.
	if game and getattr(game, "timer", None):
		game.timer(update, context)
	else:
		# Default 1 minute y mensaje vacio
		try:
			minutos = int(args[0]) if len(args) > 0 else 1
			mensaje = " ".join(args[1:]) if len(args) > 1 else ""
		except Exception:
			minutos = 1
			mensaje = ""
		
		if minutos <= 1:
			msg = 'Se pone timer para {} segundos!'.format(minutos*60)
		elif minutos <= 60:
			msg = 'Se pone timer para {} minutos!'.format(minutos)
		else:
			msg = 'Se pone timer para {} horas!'.format(minutos/60)

		bot.send_message(chat_id=update.message.chat_id, text=msg)
		job_queue.run_once(callback_alarm, minutos*60, context=[update.message.chat_id, mensaje])

def callback_alarm(context: CallbackContext):
	job = context.job
	cid = job.context[0]
	mensaje = job.context[1]
	if mensaje == "":
		context.bot.send_message(cid, '‼‼*El tiempo ha terminado*‼‼', ParseMode.MARKDOWN)
	else:
		context.bot.send_message(cid, '‼‼*Acordate de {}*‼‼'.format(mensaje), ParseMode.MARKDOWN)

def command_leave(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	log.info('command_cancelgame called {}'.format(args))
	cid = update.message.chat_id
	uid = update.effective_user.id

	game = get_game(cid)

	if not game:
		bot.send_message(cid, '‼‼*No hay juego del que salir*‼‼', ParseMode.MARKDOWN)
	else:
		if game.board:
			bot.send_message(cid, '‼‼*El juego ya empezo y el admin no permite salir de juegos*‼‼', ParseMode.MARKDOWN)
		else:
			del game.playerlist[uid]
			bot.send_message(cid, '‼‼*Has salido exitosamente del juego*‼‼', ParseMode.MARKDOWN)

def command_noticias(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('command_noticias called')
	cid = update.message.chat_id
	x = requests.get('https://www.lanacion.com.ar/')
	#print(x.text)
	soup = BeautifulSoup(x.text, features="html.parser")
	text = ""
	textContinue = ""
	for a in soup.find_all("section", {"class": "mod-description"}):
		nombre = a.find("a", {"class": "com-link"})
		# precio = a.find("div", {"class": "precioAhora"}) 
		x = f"{nombre.text}"
		textContinue = "" 
		if len(text) < 3500:
			text += x + "\n"
		else:
			textContinue += x + "\n"
	# for a in soup.find_all("div", {"class": "producto"}):
	# 	nombre = a.find("div", {"class": "nombre"})
	# 	precio = a.find("div", {"class": "precioAhora"}) 
	# 	producto = f"{nombre.text} {precio.text}"
	# 	textContinue = "" 
	# 	if len(text) < 3500:
	# 		text += producto + "\n"
	# 	else:
	# 		textContinue += producto + "\n"

	bot.send_message(cid, text, ParseMode.MARKDOWN)
	if len(textContinue) > 0:
		bot.send_message(cid, textContinue, ParseMode.MARKDOWN)

def command_image(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id

	hti = Html2Image(size=(500, 200))
	html = """<h1> An interesting title </h1> This page will be red"""
	css = "body {background: red;}"
	path_saved = hti.screenshot(html_str=html, css_str=css, save_as='red_page.png')
	log.info(path_saved)
	bot.send_photo(cid, photo=open(path_saved[0], 'rb'))



@restricted
def command_admin_games(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	uid = update.effective_user.id
	all_games_unfiltered = MainController.getGamesByTipo("Todos")	
	# Me improtan los juegos que; Este el jugador, hayan sido iniciados, datinivote no sea null y que cumpla reglas del tipo de juego en particular
	all_games = {key: "{} {}: {}".format(game.groupName, game.cid, game.tipo) for key, game in all_games_unfiltered.items() }
	msg = "Elija juego que quieras eliminar"
	simple_choose_buttons(bot, cid, uid, uid, "chooseGameDelete", msg, all_games, False, 1)

def callback_game_delete(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_game_delete called')
	callback = update.callback_query
	
	regex = re.search(r"(-?[0-9]*)\*chooseGameDelete\*(.*)\*(-?[0-9]*)", callback.data)
	opcion, uid = regex.group(2), int(regex.group(3))
	cid = int(opcion)
	delete_game(cid)
	if cid in GamesController.games.keys():
		del GamesController.games[cid]
	bot.send_message(uid, "Juego eliminado")

@restricted
def command_kick(update: Update, context: CallbackContext):
	cid = update.message.chat_id
	args = context.args
	game = get_game(cid)
	bot = context.bot
	if game:
		player = game.find_player(args[0])
		if player and hasattr(game, 'player_leaving'):
			resultado = game.player_leaving(player)
			if resultado:
				bot.send_message(cid, text=resultado)
		else:
			bot.send_message(cid, text="El jugador no esta en el partido o el juego no sabe como hecharlo.")
	else:
		bot.send_message(cid, text="No hay juego del que kickear a alguien")


	