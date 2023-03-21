#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Eduardo Peluffo"

import json
import logging as log
import random
import re
from random import randrange, choice
from time import sleep

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update, ForceReply, Update
from telegram.ext import (Updater, CommandHandler, CallbackQueryHandler, CallbackContext)

from Utils import get_game, save
from Constants.Cards import playerSets, actions
from Constants.Config import TOKEN, STATS, ADMIN
from Boardgamebox.Game import Game
from Boardgamebox.Player import Player
from Boardgamebox.Board import Board

from Utils import (next_player_after_active_player, remove_same_elements_dict,  increment_player_counter, get_config_data, player_call, simple_choose_buttons)

import GamesController
import datetime

import os
import psycopg2
import urllib.parse

# Enable logging

log.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=log.INFO)


logger = log.getLogger(__name__)

debugging = False

def init_game(bot, game):
	try:
		log.info('init_just_one called')		
		game.shuffle_player_sequence()		
		# Seteo las palabras	
		call_dicc_buttons(bot, game)
	except Exception as e:
		bot.send_message(game.cid, 'No se ejecuto el comando debido a: '+str(e))

def call_dicc_buttons(bot, game):
	#log.info('call_dicc_buttons called')
	opciones_botones = { 
		"original" : "Español Nuestro",
		"ficus" : "Español Ficus",
		"community" : "Español Community",
		"edespañola"  : "Original Ed Española",
		"german" : "Español Ed Germán",
		"futbol" : "Futbol ed Germán"
	}
	simple_choose_buttons(bot, game.cid, 1234, game.cid, "choosedicc", "¿Elija un diccionario para jugar?", opciones_botones)
		
def callback_finish_config_justone(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_finish_config_justone called')
	callback = update.callback_query
	try:
		regex = re.search(r"(-[0-9]*)\*choosedicc\*(.*)\*([0-9]*)", callback.data)
		cid, opcion, uid,  = int(regex.group(1)), regex.group(2), int(regex.group(3))
		mensaje_edit = "Has elegido el diccionario: {0}".format(opcion)
		try:
			bot.edit_message_text(mensaje_edit, cid, callback.message.message_id)
		except Exception as e:
			bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)
			
		game = get_game(cid)
		game.configs['diccionario'] = opcion
		finish_config(bot, game)
	except Exception as e:
		bot.send_message(ADMIN[0], 'No se ejecuto el comando debido a: '+str(e))
		bot.send_message(ADMIN[0], callback.data)

# list_total lista con todos los elementos
# list_a_restar Elementos a restar a list_total
def list_menos_list(list_total, list_a_restar):
	return [x for x in list_total if x not in list_a_restar]
		
def finish_config(bot, game):
	log.info('finish_config called')
	# Si vengo de un partido anterior agrego los descartes de la partida anterior.	
	if game.configs.get('discards', None):
		game.board.discards = game.configs.get('discards')
		del game.configs['discards']
	fill_cartas(game)
	game.board.state.progreso = 0
	start_round_just_one(bot, game)

def fill_cartas(game):
	opcion = game.configs['diccionario']
	url_palabras_posibles = '/JustOne/txt/spanish-{0}.txt'.format(opcion)	
	with open(url_palabras_posibles, 'r') as f:
		palabras_posibles = f.readlines()
		palabras_posibles_no_repetidas = list_menos_list(palabras_posibles, game.board.discards)
		# Si no hay palabra posible no repetidas para jugar mezclo todas las palabras posibles
		if len(palabras_posibles_no_repetidas) < 13:
		    # Quedo bien 
			game.board.discards = []
			palabras_posibles_no_repetidas = palabras_posibles
		
		random.shuffle(palabras_posibles_no_repetidas)		
		game.board.cartas = palabras_posibles_no_repetidas[0:13]
		game.board.cartas = [w.replace('\n', '') for w in game.board.cartas]

def start_round_just_one(bot, game):
	log.info('start_round_just_one called')
	cid = game.cid	
	# Se marca al jugador activo
	
	#Reseteo los votos	
	game.board.state.last_votes = {}
	game.board.state.removed_votes = {}
	
	active_player = game.player_sequence[game.board.state.player_counter]
	reviewer_player = game.player_sequence[next_player_after_active_player(game)]
	game.board.state.active_player = active_player
	game.board.state.reviewer_player = reviewer_player
	# Le muestro a los jugadores la palabra elegida para el jugador actual
	
	palabra_elegida = game.board.cartas.pop(0)
	game.board.state.acciones_carta_actual = palabra_elegida	
	
	bot.send_message(cid, game.board.print_board(game), ParseMode.MARKDOWN)	
	game.dateinitvote = datetime.datetime.now()
	call_players_to_clue(bot, game)			
	game.dateinitvote = datetime.datetime.now()
	game.board.state.fase_actual = "Proponiendo Pistas"
	save(bot, game.cid)

def call_players_to_clue(bot, game):
	for uid in game.playerlist:
		if uid != game.board.state.active_player.uid:
			#bot.send_message(cid, "Enviando mensaje a: %s" % game.playerlist[uid].name)
			mensaje = "Nueva palabra en el grupo {1}.\nAdivina el jugador: *{2}*\nLa palabra es: *{0}*, propone tu pista!".format(game.board.state.acciones_carta_actual, game.group_link_name(), game.board.state.active_player.name)
			bot.send_message(uid, mensaje, ParseMode.MARKDOWN)
			mensaje = "/clue Ejemplo" if game.board.num_players != 3 else "/clue Ejemplo Ejemplo2"
			bot.send_message(uid, mensaje)
	
def review_clues(bot, game):
	log.info('review_clues called')
	game.dateinitvote = None
	game.board.state.fase_actual = "Revisando Pistas"
	reviewer_player = game.board.state.reviewer_player
	bot.send_message(game.cid, "El revisor {0} esta viendo las pistas".format(reviewer_player.name), ParseMode.MARKDOWN)
	# Antes de enviar las pistas elimino las que son iguales no importa el case
	votes_before_method = len(game.board.state.last_votes)
	# En removed_votes guardo las cartas eliminadas		
	game.board.state.last_votes, game.board.state.removed_votes = remove_same_elements_dict(game.board.state.last_votes)
	votes_after_method = len(game.board.state.last_votes)	
	if votes_before_method > votes_after_method:
		bot.send_message(game.cid, "Se han eliminado automaticamente *{0}* pistas".format(votes_before_method-votes_after_method), ParseMode.MARKDOWN)
	
	if game.board.state.last_votes:
		send_reviewer_buttons(bot, game)
		save(bot, game.cid)
	else:
		bot.send_message(game.cid, "Todas las pistas han sido descartadas. Se pasa al siguiente jugador")
		bot.send_message(game.cid, "La palabra era: *{0}*.\n".format(game.board.state.acciones_carta_actual), ParseMode.MARKDOWN)			
		start_next_round(bot, game, True)

def send_reviewer_buttons(bot, game):
	log.info('send_reviewer_buttons called')
	reviewer_player = game.board.state.reviewer_player
	# Armo los botones para que el reviewer los analice.
	btns = []
	# Creo los botones para elegir al usuario
	cid = game.cid
	uid = reviewer_player.uid
	comando_callback = 'rechazar'
	mensaje_pregunta = "Partida {0}. Pista *{2}*.\nElija las palabras para anularlas o Finalizar para enviar las pistas restantes al jugador activo\n{1}".format(game.group_link_name(), get_pistas_eliminadas(game), game.board.state.acciones_carta_actual)
	
	# Se ponen todos los botones de pistas que no fueron eliminadas al momento.
	for uid_pista, value in game.board.state.last_votes.items():
		txtBoton = value
		datos = str(cid) + "*" + comando_callback + "*" + str(uid_pista)
		btns.append([InlineKeyboardButton(txtBoton, callback_data=datos)])		
	comando_callback = 'finalizar'
	datos = str(cid) + "*" + comando_callback + "*" + str("finalizar") + "*" + str(uid)
	btns.append([InlineKeyboardButton('Finalizar', callback_data=datos)])	
	btnMarkup = InlineKeyboardMarkup(btns)	
	bot.send_message(uid, mensaje_pregunta, parse_mode=ParseMode.MARKDOWN, reply_markup=btnMarkup)	
	save(bot, game.cid)
	
def callback_review_clues(update: Update, context: CallbackContext):
	bot = context.bot
	try:
		callback = update.callback_query
		log.info('review_clues_callback called: %s' % callback.data)
		regex = re.search(r"(-[0-9]*)\*rechazar\*([0-9]*)", callback.data)
		cid, uid_pista = int(regex.group(1)), int(regex.group(2))
		uid = update.effective_user.id
		
		game = get_game(cid)
		opcion = game.board.state.last_votes[uid_pista]

		mensaje_edit = "Has eliminado la pista: %s" % opcion
		try:
			bot.edit_message_text(mensaje_edit, cid, callback.message.message_id)
		except Exception as e:
			bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)		
		
		
		reviewer_player = game.board.state.reviewer_player
		# Remuevo las pistas que son iguales a la elegida
		
		try:
			game.board.state.removed_votes.update({key:val for key, val in game.board.state.last_votes.items() if val == opcion})					
		except Exception as e:
			bot.send_message(ADMIN[0], 'Fallo al usar removed_votes: '+str(e))
			game.board.state.amount_shuffled.update({key:val for key, val in game.board.state.last_votes.items() if val == opcion})
				
		game.board.state.last_votes = {key:val for key, val in game.board.state.last_votes.items() if val != opcion}	
		
		bot.send_message(game.cid, "El revisor %s ha descartado una pista" % reviewer_player.name)
		save(bot, game.cid)
		
		# Si todavia hay pistas...
		if game.board.state.last_votes:
			send_reviewer_buttons(bot, game)
		else:
			bot.send_message(game.cid, "Todas las pistas han sido descartadas. Se pasa al siguiente jugador")
			bot.send_message(game.cid, "La palabra era: *{0}*.\n".format(game.board.state.acciones_carta_actual), ParseMode.MARKDOWN)			
			start_next_round(bot, game, True)
	except Exception as e:
		bot.send_message(ADMIN[0], callback.data)
		raise e
		
	
def callback_review_clues_finalizado(update: Update, context: CallbackContext):
	bot = context.bot
	callback = update.callback_query
	log.info('review_clues_finalizado_callback called: %s' % callback.data)	
	regex = re.search(r"(-[0-9]*)\*finalizar\*(.*)\*([0-9]*)", callback.data)
	cid, uid = int(regex.group(1)), int(regex.group(3))
	game = get_game(cid)		
	mensaje_edit = "Has finalizado la revision"
	bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)
		
	reviewer_player = game.board.state.reviewer_player
	bot.send_message(game.cid, "El revisor %s ha terminado de revisar las pistas" % reviewer_player.name)
	send_clues(bot, game)
	save(bot, game.cid)

def callback_reviewer_confirm(update: Update, context: CallbackContext):
	bot = context.bot
	try:
		callback = update.callback_query
		log.info('review_clues_finalizado_callback called: %s' % callback.data)	
		regex = re.search(r"(-[0-9]*)\*reviewerconfirm\*(.*)\*([0-9]*)", callback.data)
		cid, opcion, uid = int(regex.group(1)), regex.group(2), int(regex.group(3))
		game = get_game(cid)
		#send_clues(bot, game)			
		
		mensaje_edit = "Gracias!"
		try:
			bot.edit_message_text(mensaje_edit, cid, callback.message.message_id)
		except Exception as e:
			bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)

		reviewer_player = game.board.state.reviewer_player

		if game.board.state.fase_actual != "Adivinando" or reviewer_player.uid != update.effective_user.id:
			# Si no se esta en la fase de adivinar o el jugador no es el revisor no se hace nada
			return

		bot.send_message(game.cid, "El revisor {0} ha determinado que es {1}".format(reviewer_player.name, opcion))
		bot.send_message(game.cid, "La palabra era: *{0}*.".format(game.board.state.acciones_carta_actual), ParseMode.MARKDOWN)
		failed = False
		if opcion == "correcto":
			game.board.state.progreso += 1
			game.board.discards.append(game.board.state.acciones_carta_actual)
		else:
			# Se elimina la proxima carta del mazo.
			game.board.discards.append(game.board.state.acciones_carta_actual)
			failed = True
			# Solo descarto si hay cartas
			if len(game.board.cartas) != 0:
				bot.send_message(game.cid, "Se ha *eliminado del mazo 1 carta* como penalización", ParseMode.MARKDOWN)			
				game.board.discards.append(game.board.cartas.pop(0))
			else:
				# Si se falla en la ultima carta la penalizacion es perder 1 punto
				bot.send_message(game.cid, "Se ha *perdido 1 punto* como penalización", ParseMode.MARKDOWN)
				game.board.state.progreso -= 1		
		start_next_round(bot, game, failed)
	except Exception as e:
		bot.send_message(game.cid, 'No se ejecuto el comando debido a: '+str(e))

def send_clues(bot, game):
	text = ""
	for key, value in game.board.state.last_votes.items():		
		try:
			player = game.playerlist[key]
		except Exception:
			# Jugando de a 3 uso el key y key-1 para las dos pistas si no esta bien entonces la pista es anonima
			if game.board.num_players == 3:
				player = game.playerlist[key-1]
			else:
				player = Player("Anonimo", key)
			
		text += "*{1}: {0}*\n".format(value, player.name)
	
	mensaje_final = "[{0}](tg://user?id={1}) es hora de adivinar! Pone /guess Palabra o /pass si no sabes la palabra\nLas pistas son: \n{2}\n*NO SE PUEDE HABLAR*".format(game.board.state.active_player.name, game.board.state.active_player.uid, text)
	
	game.board.state.fase_actual = "Adivinando"
	save(bot, game.cid)
	
	bot.send_message(game.cid, mensaje_final, ParseMode.MARKDOWN)

def pass_just_one(bot, game):
	bot.send_message(game.cid, "La palabra era: *{0}*.".format(game.board.state.acciones_carta_actual), ParseMode.MARKDOWN)
	game.board.discards.append(game.board.state.acciones_carta_actual)
	failed = True
	# Solo descarto si hay cartas
	'''
	if len(game.board.cartas) != 0:
		bot.send_message(game.cid, "Se ha *eliminado del mazo 1 carta* como penalización", ParseMode.MARKDOWN)			
		game.board.discards.append(game.board.cartas.pop(0))
	else:
		# Si se falla en la ultima carta la penalizacion es perder 1 punto
		bot.send_message(game.cid, "Se ha *perdido 1 punto* como penalización", ParseMode.MARKDOWN)
		game.board.state.progreso -= 1
	'''
	start_next_round(bot, game, failed)	

def get_pistas_eliminadas(game):
	text_eliminadas = ""
	if game.board.state.removed_votes:
		text_eliminadas += "*Pistas eliminadas*\n"
		for key, value in game.board.state.removed_votes.items():
			try:
				player = game.playerlist[int(key)]
			except Exception:
				player = game.playerlist[int(key)-1]

			text_eliminadas += "*{1}: {0}*\n".format(value, player.name)
	return text_eliminadas

def informar_pistas_eliminadas(bot, game):
	try:
		#bot.send_message(ADMIN[0], game.board.state.removed_votes)
		text_eliminadas = get_pistas_eliminadas(game)
		log.info(text_eliminadas)
		bot.send_message(game.cid, text_eliminadas, ParseMode.MARKDOWN)
	except Exception as e:
		log.info(f"{game.cid} No se ejecuto el comando debido a: " +str(e))


def start_next_round(bot, game, failed = False):
	log.info('start_next_round called')	
	if game.board.state.removed_votes:
		informar_pistas_eliminadas(bot, game)
	log.info('Verifing End_Game called')
	if (not game.board.cartas and game.modo != 'Extreme') or (game.modo == 'Extreme' and failed):
		# Si no quedan cartas se termina el juego y se muestra el puntaje.
		mensaje = "Juego finalizado! El puntaje fue de: *{0}*".format(game.board.state.progreso)		
		game.board.state.fase_actual = "Finalizado"
		save(bot, game.cid)
		bot.send_message(game.cid, mensaje, ParseMode.MARKDOWN)
		continue_playing(bot, game)
		#bot.send_message(game.cid, "Para comenzar un juego nuevo pon el comando /delete y luego /newgame", ParseMode.MARKDOWN)
		return
	# Si se acabaron las cartas y esta en extreme agrego mas.
	if not game.board.cartas:
		fill_cartas(game)
	increment_player_counter(game)
	start_round_just_one(bot, game)

def continue_playing(bot, game):
	opciones_botones = { "Nuevo" : "Nuevo Partido con nuevos jugadores", "Mismo Diccionario" : "Mismo diccionario", "Otro Diccionario" : "Diferente diccionario"}
	msg = "¿Quieres continuar jugando? *Modo actual {}*. Si quieres cambiar de modo debes elegir nuevo partido".format(game.modo)
	simple_choose_buttons(bot, game.cid, 1, game.cid, "chooseend", msg, opciones_botones)
	
def callback_finish_game_buttons(update: Update, context: CallbackContext):
	bot = context.bot
	callback = update.callback_query
	try:		
		#log.info('callback_finish_game_buttons called: %s' % callback.data)	
		regex = re.search(r"(-[0-9]*)\*chooseend\*(.*)\*([0-9]*)", callback.data)
		cid, opcion, uid = int(regex.group(1)), regex.group(2), int(regex.group(3))
		mensaje_edit = "Has elegido el diccionario: {0}".format(opcion)
		try:
			bot.edit_message_text(mensaje_edit, cid, callback.message.message_id)
		except Exception as e:
			bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)				
		game = get_game(cid)
		
		# Obtengo el diccionario actual, primero casos no tendre el config y pondre el community
		try:
			dicc = game.configs.get('diccionario','edespañola')
		except Exception as e:
			dicc = 'community'
		
		# Obtengo datos de juego anterior		
		groupName = game.groupName
		tipojuego = game.tipo
		modo = game.modo
		descarte = game.board.discards
		# Pongo el link asi no lo pierdo cuando comienza otra partida
		link = game.configs.get('link', None)
		# Dependiendo de la opcion veo que como lo inicio
		players = game.playerlist.copy()
		# Creo nuevo juego
		game = Game(cid, uid, groupName, tipojuego, modo)
		GamesController.games[cid] = game
		# Guarda los descartes en configs para asi puedo recuperarlos
		game.configs['discards'] = descarte
		#Persisto el nuevo link
		game.configs['link'] = link

		if opcion == "Nuevo":
			bot.send_message(cid, "Cada jugador puede unirse al juego con el comando /join.\nEl iniciador del juego (o el administrador) pueden unirse tambien y escribir /startgame cuando todos se hayan unido al juego!")			
			return
		#log.info('Llego hasta la creacion')		
		game.playerlist = players
		# StartGame
		player_number = len(game.playerlist)
		game.board = Board(player_number, game)		
		game.player_sequence = []
		game.shuffle_player_sequence()
					
		if opcion == "Mismo Diccionario":
			#(Beta) Nuevo Partido, mismos jugadores, mismo diccionario
			#log.info('Llego hasta el new2')
			game.configs['diccionario'] = dicc
			finish_config(bot, game)
		if opcion == "Otro Diccionario":
			#(Beta) Nuevo Partido, mismos jugadores, diferente diccionario
			call_dicc_buttons(bot, game)				
	except Exception as e:
		bot.send_message(ADMIN[0], 'No se ejecuto el comando debido a: '+str(e))
		bot.send_message(ADMIN[0], callback.data)

def myturn_message(game, uid):
	try:
		group_link_name = game.group_link_name()
		if game.board.state.fase_actual == "Proponiendo Pistas":			
			mensaje_clue_ejemplo = "/clue Ejemplo" if game.board.num_players != 3 else "/clue Ejemplo Ejemplo2"
			return "Partida: {} debes dar {} para la palabra: *{}*.\nAdivina el jugador *{}*".format(group_link_name, mensaje_clue_ejemplo, game.board.state.acciones_carta_actual, game.board.state.active_player.name)
		elif game.board.state.fase_actual == "Revisando Pistas":
			return "Partida: {} Revisor recorda que tenes que verificar las pistas".format(group_link_name)
		elif game.board.state.fase_actual == "Adivinando":			
			return "Partida: {} estamos esperando para que hagas /guess EJEMPLO o /pass".format(group_link_name)
	except Exception as e:
		return str(e)
		
