import json
import logging as log
import datetime
#import ast
import os
import psycopg2
import urllib.parse
import sys
from time import sleep

import Unanimo.Controller as UnanimoController
from Utils import get_game, save

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update, ForceReply, Update
from telegram.ext import (CallbackContext)

import GamesController
from Constants.Config import ADMIN

from Utils import player_call, simple_choose_buttons

# from PIL import Image
# from io import BytesIO

import re
# Objetos que uso de prueba estaran en el state

# Enable logging

log.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=log.INFO)
logger = log.getLogger(__name__)

#DB Connection I made a Haroku Postgres database first
urllib.parse.uses_netloc.append("postgres")
url = urllib.parse.urlparse(os.environ["DATABASE_URL"])

# conn = psycopg2.connect(
#     database=url.path[1:],
#     user=url.username,
#     password=url.password,
#     host=url.hostname,
#     port=url.port
# )

		
def command_call(bot, game):
	# Verifico en mi maquina de estados que comando deberia usar para el estado(fase) actual
	if game.board.state.fase_actual == "Proponiendo Pistas":
		call_proponiendo_pistas(bot, game)
	elif game.board.state.fase_actual == "Revisando Pistas":
		reviewer_player = game.board.state.reviewer_player
		bot.send_message(game.cid, "Revisor {0} recorda que tenes que verificar las pistas".format(player_call(reviewer_player)), ParseMode.MARKDOWN)
		UnanimoController.send_reviewer_buttons(bot, game)
	elif game.board.state.fase_actual == "Adivinando":
		active_player = game.board.state.active_player
		bot.send_message(game.cid, "{0} estamos esperando para que hagas /guess EJEMPLO o /pass".format(player_call(active_player)), ParseMode.MARKDOWN)
	

def call_proponiendo_pistas(bot, game):
	if not game.dateinitvote:
		# If date of init vote is null, then the voting didnt start          
		bot.send_message(game.cid, "No es momento de dar pista.")
	else:
		#If there is a time, compare it and send history of votes.
		start = game.dateinitvote
		stop = datetime.datetime.now()          
		elapsed = stop - start
		if elapsed > datetime.timedelta(minutes=1):
			# Only remember to vote to players that are still in the game
			history_text = ""
			for player in game.player_sequence:
				# If the player is not in last_votes send him reminder
				if player.uid not in game.board.state.last_votes:
					history_text += "Tienes que dar tus palabras representativas {0}.\n".format(player_call(player))
					# Envio mensaje inicial de pistas para recordarle al jugador la pista y el grupo
					mensaje = "Palabra en el grupo {1}.\nAdivina el jugador: *{2}*\nLa palabra es: *{0}*, propone tus palabras representativas!".format(game.board.state.acciones_carta_actual, game.group_link_name(), game.board.state.active_player.name)
					bot.send_message(player.uid, mensaje, ParseMode.MARKDOWN)
					mensaje = "Ejemplo: Si la palabra fuese (Fiesta)\n/words Cumpleaños, Torta, Decoracion, Musica, Rock, Infantil, Luces, Velas"
					bot.send_message(player.uid, mensaje)
			if len(history_text) > 0:
				bot.send_message(game.cid, history_text, ParseMode.MARKDOWN)
			# Se pone >= ya que si un jugador se va del partido y ya puso pista entonces vale
			if game.board.num_players != 3 and len(game.board.state.last_votes) >= len(game.player_sequence):
				UnanimoController.review_clues(bot, game)			
		else:
			bot.send_message(game.cid, "5 minutos deben pasar para llamar a call") 

def validateAndFormat(words):
	# list(set()) remueve duplicados
	words_list = list(set(words.replace(", ", ",").title().split(",")))
	words_list.sort()
	return ','.join(words_list)

def set_words(bot, args):
	game = get_game(int(args[1]))
	uid = args[2]
	if uid in game.playerlist:
		#Check if there is a current game
		if game.board == None:
			bot.send_message(game.cid, "El juego no ha comenzado!")
			return					
		if game.board.state.fase_actual == "Proponiendo Pistas":
			
			player_words = validateAndFormat(args[0])
			bot.send_message(uid, "Tu pista: " + player_words.replace(',', ', ') + "fue agregada a las pistas.")	
			# Agrego las palabras del usuario al diccionario		
			game.board.state.last_votes[uid] = player_words
			
			save(bot, game.cid)
			# Verifico si todos los jugadores -1 pusieron pista
			bot.send_message(game.cid, "El jugador *%s* ha puesto una pista." % game.playerlist[uid].name, ParseMode.MARKDOWN)
			
			if len(game.board.state.last_votes) == len(game.player_sequence):
				UnanimoController.review_clues(bot, game)
			# if game.board.num_players != 3:
			# 	if len(game.board.state.last_votes) == len(game.player_sequence)-1:
			# 		UnanimoController.review_clues(bot, game)
			# else:
			# 	# De a 3 jugadores exigo que pongan 2 pistas cada uno son 4 de a 3 jugadores
			# 	if len(game.board.state.last_votes) == len(game.player_sequence)+1:
			# 		UnanimoController.review_clues(bot, game)
		else:
			bot.send_message(uid, "No puedes hacer dar clue si vos tenes que adivinar o ya ha pasado la fase de poner pistas.")
	else:
		bot.send_message(uid, "No puedes hacer clue si no estas en ningun partido.")

def command_points(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	cid = update.message.chat_id
	game = get_game(cid)
	if not game or game.tipo != 'Unanimo':
		bot.send_message(cid, 'Aca no hay juego de Unanimo', ParseMode.MARKDOWN)
		return
	# Valido que hayan pasado 2+ datos
	if len(args) >= 2:
		bot.send_message(cid, 'El comando es /points Leviatas -1 o /points Leviatas 2', ParseMode.MARKDOWN)
		return
	try:
		puntos = int(args[-1])
		player = game.find_player(args[0:len(args)-1])
		if not player:
			bot.send_message(cid, f'El jugador *{args[0:len(args)-1]}* no existe', ParseMode.MARKDOWN)
			return
		player.points += puntos
		save(bot, game.cid)
	except ValueError:
		int()

def command_words(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	# try:		
	#Send message of executing command   
	try:			
		cid = update.message.chat_id
		uid = update.message.from_user.id
	except Exception as e:
		cid = args[1]
		uid = args[2]
	
	# Si no se esta enviando al bot le borro el mensaje
	if update.effective_message.chat.type in ['group', 'supergroup']:
		bot.delete_message(cid, update.message.message_id)
		return

	# Para simplificar mando el CHAT_ID del partido junto con la pista
	# Permito las dos formas de gregar pistas
	
	if len(args) > 0:
		# Obtengo todos los juegos de base de datos de los que usan clue
		mensaje_error = ""
		conn = psycopg2.connect(
			database=url.path[1:],
			user=url.username,
			password=url.password,
			host=url.hostname,
			port=url.port
		)
		cursor = conn.cursor()			
		log.info("Executing in DB")
		query = "select * from games g where g.tipojuego = 'Unanimo'"
		cursor.execute(query)
		# Si encuentra partida...
		if cursor.rowcount > 0:					
			for table in cursor.fetchall():
				# Por cada partida encontrada la cargo en games si no esta en el controller.
				#bot.send_message(uid, table[0])
				if table[0] not in GamesController.games.keys():
					#bot.send_message(uid, "Cargando el juego {0}".format(table[0]))
					get_game(table[0])
			clue_games_restriction = ['Unanimo']
			#bot.send_message(uid, "Obtuvo esta cantidad de juegos: {0}".format(len(GamesController.games)))
			clue_games = {key:val for key, val in GamesController.games.items() if val.tipo in clue_games_restriction}
			btns = []
			#bot.send_message(uid, len(clue_games))rdd
			
			for game_chat_id, game in clue_games.items():
				#bot.send_message(uid, "Creando boton para el juego {0}".format(game_chat_id))
				# try:
				if uid in game.playerlist and game.board != None:
					if game.board.state.fase_actual == "Proponiendo Pistas":
						clue_text = replace_accent(' '.join(args))
						cid = game_chat_id
						# Creo el boton el cual eligirá el jugador
						txtBoton = game.groupName
						comando_callback = "choosegamewords"
						context.user_data[uid] = clue_text
						datos = str(game_chat_id) + "*" + comando_callback + "*pista*" + str(uid)
						btns.append([InlineKeyboardButton(txtBoton, callback_data=datos)])
				# except Exception as e:
				# 	game.groupName
				# 	bot.send_message(ADMIN[0], f"En el juego [{game.groupName}] ha habido un error")
				# 	bot.send_message(ADMIN[0], str(e))
			#bot.send_message(uid, "Llego a botones")
			# Despues de recorrer los partidos y verificar si el usuario puede poner pista le pregunto
			if len(btns) != 0:
				if len(btns) == 1:
					#Si es solo 1 juego lo hago automatico
					set_words(bot, [replace_accent(' '.join(args)), cid, uid])
				else:
					txtBoton = "Cancel"
					datos = "-1*choosegamewords*pista*" + str(uid)
					btns.append([InlineKeyboardButton(txtBoton, callback_data=datos)])
					btnMarkup = InlineKeyboardMarkup(btns)
					bot.send_message(uid, "En cual de estos grupos queres mandar la pista?", reply_markup=btnMarkup)
			else:
				mensaje_error = "No hay partidas en las que puedas hacer /words"
				bot.send_message(uid, mensaje_error)
					
		else:
			mensaje_error = "No hay partidas vivas en las que puedas hacer /words"
			bot.send_message(cid, mensaje_error)
		conn.close()
	else:
		bot.send_message(cid, "Le faltan/sobran argumentos recuerde que es /words [Palabra1, Palabra2, Palabra8]. Ej: /words Cumpleaños, Torta, Decoracion, Musica, Rock, Infantil, Luces, Velas")
	# except Exception as e:
	# 	game.groupName
	# 	bot.send_message(ADMIN[0], f"En el juego {game.groupName} ha habido un error")
	# 	bot.send_message(ADMIN[0], str(e))
		#raise

def callback_choose_game_clue(update: Update, context: CallbackContext):
	bot = context.bot
	callback = update.callback_query
	log.info('callback_choose_mode called: %s' % callback.data)	
	regex = re.search(r"(-[0-9]*)\*choosegamewords\*(.*)\*([0-9]*)", callback.data)
	cid, uid = int(regex.group(1)), int(regex.group(3)),
	
	if cid == -1:
		bot.edit_message_text("Cancelado", uid, callback.message.message_id)
		return
	
	game = get_game(cid)
	mensaje_edit = "Has elegido el grupo {0}".format(game.groupName)
	
	opcion = context.user_data[uid]

	bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)
	set_words(bot, [opcion, cid, uid])

def replace_accent(txt):
	acentos = [("á", "a"),("é", "e"),("í", "i"),("ó","o"),("ú","u")]
	for acento in acentos:
		txt = txt.replace(acento[0], acento[1])
	return txt

def command_continue(bot, game, uid):
	try:
		
		# Verifico en mi maquina de estados que comando deberia usar para el estado(fase) actual
		if game.board.state.fase_actual == "Proponiendo Pistas":
			# Vuelvo a mandar la pista
			UnanimoController.call_players_to_clue(bot, game)
		elif game.board.state.fase_actual == "Revisando Pistas":
			UnanimoController.review_clues(bot, game)
		elif game.board.state.fase_actual == "Adivinando":
			active_player = game.board.state.active_player
			bot.send_message(game.cid, "{0} estamos esperando para que hagas /guess EJEMPLO o /pass".format(player_call(active_player)), ParseMode.MARKDOWN)
		elif game.board.state.fase_actual == "Finalizado":
			UnanimoController.continue_playing(bot, game)
	except Exception as e:
		bot.send_message(game.cid, str(e))
		
def command_continue(bot, game, uid):
	try:
		
		# Verifico en mi maquina de estados que comando deberia usar para el estado(fase) actual
		if game.board.state.fase_actual == "Proponiendo Pistas":
			# Vuelvo a mandar la pista
			UnanimoController.call_players_to_clue(bot, game)
		elif game.board.state.fase_actual == "Revisando Pistas":
			UnanimoController.review_clues(bot, game)
		elif game.board.state.fase_actual == "Adivinando":
			active_player = game.board.state.active_player
			bot.send_message(game.cid, "{0} estamos esperando para que hagas /guess EJEMPLO o /pass".format(player_call(active_player)), ParseMode.MARKDOWN)
		elif game.board.state.fase_actual == "Finalizado":
			UnanimoController.continue_playing(bot, game)
	except Exception as e:
		bot.send_message(game.cid, str(e))
