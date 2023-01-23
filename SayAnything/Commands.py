import logging as log
import datetime
#import ast
import jsonpickle
import os
import psycopg2
import urllib.parse
import sys
from time import sleep

import SayAnything.Controller as SayAnythingController
from Utils import get_game, save

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update, ForceReply, Update
from telegram.ext import (CallbackContext)
import MainController
import GamesController
from Constants.Config import STATS
from SayAnything.Boardgamebox.Board import Board
from SayAnything.Boardgamebox.Game import Game
from SayAnything.Boardgamebox.Player import Player
from SayAnything.Boardgamebox.Vote import Vote
from Boardgamebox.State import State
from Constants.Config import ADMIN
from Utils import player_call
from collections import namedtuple
from io import BytesIO

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
# Objetos que uso de prueba estaran en el state

# Enable logging

log.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=log.INFO)
logger = log.getLogger(__name__)

def command_call(bot, game):
	try:
		# Verifico en mi maquina de estados que comando deberia usar para el estado(fase) actual
		if game.board.state.fase_actual == "Proponiendo Pistas":
			call_proponiendo_pistas(bot, game)
		elif game.board.state.fase_actual == "Adivinando":			
			bot.send_message(game.cid, SayAnythingController.get_respuestas(bot, game), ParseMode.MARKDOWN)
		elif game.board.state.fase_actual == "Votando Frases":
			if len(game.board.state.votes_on_votes) >= (len(game.player_sequence)-1)*2:
				SayAnythingController.count_points(bot, game)
			else:
				call_to_vote_respeustas(bot, game)
			
	except Exception as e:
		bot.send_message(game.cid, str(e))

def call_to_vote_respeustas(bot, game):
	call_text = 'Recuerden votar\n'
	for player in game.player_sequence:
		if verify_missing_votes_user(game, player.uid):
			lista_votos_usuario = [(index, val[2]) for index, val in 
					       enumerate(game.board.state.votes_on_votes) if val[0].uid==player.uid]
			call_text += 'Te faltan *{0}* votos {1}.\n'.format(2-len(lista_votos_usuario), player_call(player))
			SayAnythingController.send_vote_buttons(bot, game, player.uid)		
	bot.send_message(game.cid, call_text, ParseMode.MARKDOWN)	

def verify_missing_votes_user(game, uid):
	lista_votos_usuario = [(index, val[2]) for index, val in enumerate(game.board.state.votes_on_votes) if val[0].uid==uid]
	return len(lista_votos_usuario) != 2 and uid != game.board.state.active_player.uid
	
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
				# If the player is not in ordered_votes send him reminder
				voto_jugador = next((x for x in game.board.state.ordered_votes if x.player.uid == player.uid), None)
				if not voto_jugador and player.uid != game.board.state.active_player.uid:
					history_text += "Tienes que dar una respuesta {0}.\n".format(player_call(player))
					# Envio mensaje inicial de pistas para recordarle al jugador la pista y el grupo
					mensaje = "Palabra en el grupo *{1}*.\nJugador activo: *{2}*\nLa frase es: *{0}*, propone tu respuesta!".format(game.board.state.acciones_carta_actual, game.groupName, game.board.state.active_player.name)
					bot.send_message(player.uid, mensaje, ParseMode.MARKDOWN)
					mensaje = "/resp Ejemplo" if game.board.num_players != 3 else "/prop Ejemplo Ejemplo2"
					bot.send_message(player.uid, mensaje)
			bot.send_message(game.cid, history_text, ParseMode.MARKDOWN)
			if game.board.num_players != 3 and len(game.board.state.ordered_votes) == len(game.player_sequence)-1:
				SayAnythingController.send_prop(bot, game)
			elif len(game.board.state.ordered_votes) == len(game.player_sequence)+1:
				# De a 3 jugadores exigo que pongan 2 pistas cada uno son 4 de a 3 jugadores
				SayAnythingController.send_prop(bot, game)
		else:
			bot.send_message(game.cid, "5 minutos deben pasar para llamar a call") 
		
# Cada juego que tenga posibles muchos juegos cuyo dato se ponga en privado tendran que hacer un metodo diferente.
# Le paso user data para que pueda poner su propuesta sin temer 
def command_propose(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	user_data = context.user_data
	try:
		cid = update.message.chat_id
		uid = update.message.from_user.id
		if len(args) > 0:
			# Obtengo todos los juegos de base de datos de los que usan clue
			mensaje_error = ""			
			games_tipo = MainController.getGamesByTipo('SayAnything')						
			btns, cid = get_choose_game_buttons(games_tipo, uid, 
						       allow_only = "",
						       restrict = "active_player", 
						       fase_actual = 'Proponiendo Pistas', button_value = 'prop',
						       callback_command = 'choosegamepropSA')			
			user_data[uid] = ' '.join(args)
			
			if len(btns) != 0:
				if len(btns) == 1:
					#Si es solo 1 juego lo hago automatico
					game = get_game(cid)
					add_propose(bot, game, uid, ' '.join(args))
				else:
					txtBoton = "Cancel"
					datos = "-1*choosegameclue*" + "prop" + "*" + str(uid)
					btns.append([InlineKeyboardButton(txtBoton, callback_data=datos)])
					btnMarkup = InlineKeyboardMarkup(btns)
					bot.send_message(uid, "En cual de estos grupos queres mandar la pista?", reply_markup=btnMarkup)
			else:
				mensaje_error = "No hay partidas en las que puedas hacer /resp"
				bot.send_message(uid, mensaje_error)
	except Exception as e:
		bot.send_message(uid, str(e))
		log.error("Unknown error: " + str(e))

def get_choose_game_buttons(games_tipo, uid, allow_only, restrict, fase_actual, button_value, callback_command):	
	btns = []
	cid = None
	for game_chat_id, game in games_tipo.items():
		if uid in game.playerlist and game.board != None:
			# Si no se pasa nada, pongo un id que no de favorable en la consulta para mostrar juegos
			allow_only_id = getattr(getattr(game.board.state, allow_only, -1), "uid", -1)
			restrict_id = getattr(getattr(game.board.state, restrict, uid), "uid", uid)
			
			log.info("Allow {} Restrict {}".format(allow_only_id, restrict_id))
			if ((uid != restrict_id) or (uid == allow_only_id)) and game.board.state.fase_actual == fase_actual:
				clue_text = button_value
				# Pongo en cid el id del juego actual, para el caso de que haya solo 1
				cid = game_chat_id
				# Creo el boton el cual eligirá el jugador
				txtBoton = game.groupName
				comando_callback = callback_command
				datos = str(game_chat_id) + "*" + comando_callback + "*" + clue_text + "*" + str(uid)
				btns.append([InlineKeyboardButton(txtBoton, callback_data=datos)])
	return btns, cid
	
		
def callback_choose_game_prop(update: Update, context: CallbackContext):
	bot = context.bot
	user_data = context.user_data
	callback = update.callback_query
	log.info('callback_choose_game_prop called: %s' % callback.data)	
	regex = re.search(r"(-[0-9]*)\*choosegamepropSA\*(.*)\*([0-9]*)", callback.data)
	cid, uid = int(regex.group(1)), int(regex.group(3))
	
	if cid == -1:
		bot.edit_message_text("Cancelado", uid, callback.message.message_id)
		return	
	game = get_game(cid)
	mensaje_edit = "Has elegido el grupo {0}".format(game.groupName)	
	bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)	
	propuesta = user_data[uid]	
	# Obtengo el juego y le agrego la pista
	add_propose(bot, game, uid, propuesta)

def add_propose(bot, game, uid, propuesta):
	# Se verifica igual en caso de que quede una botonera perdida
	if uid in game.playerlist:
		#Check if there is a current game
		if game.board == None:
			bot.send_message(game.cid, "El juego no ha comenzado!")
			return					
		if uid == ADMIN[0] or (uid != game.board.state.active_player.uid and game.board.state.fase_actual == "Proponiendo Pistas"):	
			bot.send_message(uid, "Tu respuesta: %s fue agregada." % (propuesta))			
			#game.board.state.last_votes[uid] = propuesta
			
			# Si tiene el atributo no fue ingresado ningun voto y no fue creado. Lo creo.
			if hasattr(game.board.state, 'ordered_votes'):
				previous_vote = next((vote for vote in game.board.state.ordered_votes if vote.player.uid == uid), None)
				if previous_vote:
					game.board.state.ordered_votes.remove(previous_vote)
				game.board.state.ordered_votes.append(Vote(game.playerlist[uid], 'propuesta', propuesta))
			else:
				game.board.state.ordered_votes = []
				game.board.state.ordered_votes.append(Vote(game.playerlist[uid], 'propuesta', propuesta))
				
			save(bot, game.cid)			
			# Verifico si todos los jugadores -1 pusieron pista
			bot.send_message(game.cid, "El jugador *%s* ha ingresado una respuesta." % game.playerlist[uid].name, ParseMode.MARKDOWN)			
			# Todo cambiar a -1 cuando termine las pruebas
			if len(game.board.state.ordered_votes) == len(game.player_sequence)-1:
				SayAnythingController.send_prop(bot, game)			
		else:
			bot.send_message(uid, "No puedes proponer si sos el jugador activo o ya ha pasado la fase de poner pistas.")
	else:
		bot.send_message(uid, "No puedes hacer clue si no estas en el partido.")
		
def command_next_turn(update: Update, context: CallbackContext):
	bot = context.bot
	uid = update.message.from_user.id
	cid = update.message.chat_id
	game = get_game(cid)	
	SayAnythingController.start_next_round(bot, game)

def command_pass(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('command_pass called')
	uid = update.message.from_user.id
	cid = update.message.chat_id
	game = get_game(cid)
	
	if game.board.state.fase_actual != "Adivinando" or uid != game.board.state.active_player.uid:
		bot.send_message(game.cid, "No es el momento de adivinar o no eres el que tiene que adivinar", ParseMode.MARKDOWN)
		return
	SayAnythingController.pass_say_anything(bot, game)
	
def command_pick(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	try:
		log.info('command_pick called')
		#Send message of executing command
		cid = update.message.chat_id
		uid = update.message.from_user.id
		groupType = update.message.chat.type
		# Si el usuario no hace el pick en privado corregirlo.
		if groupType in ['group', 'supergroup']:
			bot.delete_message(cid, update.message.message_id)
			return
				
		games_tipo = MainController.getGamesByTipo('SayAnything')		
		elegido = -1 if check_invalid_pick(args) else args[0]
		
		btns, cid = get_choose_game_buttons(games_tipo, uid, 
						       allow_only = "active_player",
						       restrict = "",
						       fase_actual = 'Adivinando', button_value = elegido,
						       callback_command = 'choosegamepickSA')		
		if len(btns) != 0:
			if len(btns) == 0:
				#Si es solo 1 juego lo hago automatico
				game = get_game(cid)
				pick_resp(bot, game, uid, elegido)
			else:
				txtBoton = "Cancel"
				datos = "-1*choosegameclue*" + "prop" + "*" + str(uid)
				btns.append([InlineKeyboardButton(txtBoton, callback_data=datos)])
				btnMarkup = InlineKeyboardMarkup(btns)
				bot.send_message(uid, "¿En cual de estos grupos queres elegir respuesta?", reply_markup=btnMarkup)
		else:
			mensaje_error = "No hay partidas en las que puedas hacer /pick"
			bot.send_message(uid, mensaje_error)
		
	except Exception as e:
		bot.send_message(uid, str(e))
		log.error("Unknown error: " + str(e))

def callback_choose_game_pick(update: Update, context: CallbackContext):
	bot = context.bot
	callback = update.callback_query
	log.info('callback_choose_game_prop called: %s' % callback.data)	
	regex = re.search("(-[0-9]*)\*choosegamepickSA\*(.*)\*([0-9]*)", callback.data)
	cid, strcid, opcion, uid, struid = int(regex.group(1)), regex.group(1), regex.group(2), int(regex.group(3)), regex.group(3)	
	
	if cid == -1:
		bot.edit_message_text("Cancelado", uid, callback.message.message_id)
		return	
	game = get_game(cid)
	mensaje_edit = "Has elegido el grupo {0}".format(game.groupName)	
	bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)	
	
	# Obtengo el juego y le agrego la pista
	pick_resp(bot, game, uid, opcion)
		
# Verifica si el pick es invalido
def check_invalid_pick(args):
	return (len(args) < 1 or (not args[0].isdigit()) or args[0] == '0')
		
def pick_resp(bot, game, uid, opcion):
	try:
		log.info('pick_resp called')
		if (game.board.state.fase_actual != "Adivinando" 
		    		or uid != game.board.state.active_player.uid 
				or int(opcion) > len(game.board.state.ordered_votes) ):# and uid not in ADMIN:
			bot.send_message(game.cid, "No es el momento de adivinar, no eres el que tiene que adivinar o no has ingresado algo valido para puntuar", ParseMode.MARKDOWN)
			return
		# Llego con un numero valido, mayor a zero y que esta en el rando de las respuestas
		args_text = opcion		
		game.board.state.index_pick_resp = int(args_text)-1			
		bot.send_message(game.cid, "El jugador activo ha elegido la frase! A votar!")
		game.board.state.fase_actual = "Votando Frases"		
		if len(game.board.state.votes_on_votes) == (len(game.player_sequence)-1)*2:
			SayAnythingController.count_points(bot, game)
		else:
			command_call(bot, game)	
	except Exception as e:
		bot.send_message(uid, str(e))
		log.error("Unknown error: " + str(e))
		
def command_continue(bot, game, uid):
	try:
		
		# Verifico en mi maquina de estados que comando deberia usar para el estado(fase) actual
		if game.board.state.fase_actual == "Proponiendo Pistas":
			# Vuelvo a mandar la pista
			SayAnythingController.call_players_to_clue(bot, game)
		elif game.board.state.fase_actual == "Adivinando":
			active_player = game.board.state.active_player
			bot.send_message(game.cid, "{0} estamos esperando para que hagas /guess EJEMPLO o /pass".format(player_call(active_player)), ParseMode.MARKDOWN)
		elif game.board.state.fase_actual == "Finalizado":
			SayAnythingController.continue_playing(bot, game)
	except Exception as e:
		bot.send_message(game.cid, str(e))
