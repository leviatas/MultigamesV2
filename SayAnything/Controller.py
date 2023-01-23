#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Eduardo Peluffo"

import json
import logging as log
import random
import re
from random import randrange
from time import sleep

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update, ForceReply, Update
from telegram.ext import (Updater, CommandHandler, CallbackQueryHandler, CallbackContext)

from Utils import get_game, save, simple_choose_buttons_only_buttons
from Constants.Cards import playerSets, actions
from Constants.Config import TOKEN, STATS, ADMIN

from SayAnything.Boardgamebox.Game import Game
from SayAnything.Boardgamebox.Player import Player
from SayAnything.Boardgamebox.Board import Board

from Utils import player_call, get_config_data, increment_player_counter, simple_choose_buttons

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
		log.info('init_say_anything called')		
		game.shuffle_player_sequence()		
		# Seteo las palabras	
		call_dicc_buttons(bot, game)
	except Exception as e:
		bot.send_message(game.cid, 'No se ejecuto el comando debido a: '+str(e))

def call_dicc_buttons(bot, game):
	#log.info('call_dicc_buttons called')
	opciones_botones = { "preguntas" : "Español Ficus" }
	simple_choose_buttons(bot, game.cid, 1234, game.cid, "choosediccSA", "¿Elija un diccionario para jugar?", opciones_botones)

def callback_finish_config(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_finish_config_sayanything called')
	callback = update.callback_query
	try:
		regex = re.search("(-[0-9]*)\*choosediccSA\*(.*)\*([0-9]*)", callback.data)
		cid, strcid, opcion, uid, struid = int(regex.group(1)), regex.group(1), regex.group(2), int(regex.group(3)), regex.group(3)
		mensaje_edit = "Has elegido el diccionario: {0}".format(opcion)
		try:
			bot.edit_message_text(mensaje_edit, cid, callback.message.message_id)
		except Exception as e:
			bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)
			
		game = get_game(cid)
		game.configs['diccionario'] = opcion
		finish_config(bot, game, opcion)
	except Exception as e:
		bot.send_message(ADMIN[0], 'No se ejecuto el comando debido a: '+str(e))
		bot.send_message(ADMIN[0], callback.data)

# list_total lista con todos los elementos
# list_a_restar Elementos a restar a list_total
def list_menos_list(list_total, list_a_restar):
	return [x for x in list_total if x not in list_a_restar]
		
def finish_config(bot, game, opcion):
	log.info('finish_config called')
	if game.configs.get('discards', None):
		game.board.discards = game.configs.get('discards')
		del game.configs['discards']
	url_palabras_posibles = '/SayAnything/txt/spanish-{0}.txt'.format(opcion)	
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
	game.board.state.progreso = 0
	start_round_say_anything(bot, game)
		
def start_round_say_anything(bot, game):
	log.info('start_round_say_anything called')
	cid = game.cid
	# Se marca al jugador activo
	
	#Reseteo los votos	
	game.board.state.last_votes = {}
	game.board.state.removed_votes = {}
	game.board.state.ordered_votes = []
	# Tuplas de votos (UID=de quien es el voto, PUNTAJE=valor del voto, INDEX_ORDERED_VOTES=respeusta que apunta)  
	game.board.state.votes_on_votes = []
	game.board.state.index_pick_resp = -1
	
	active_player = game.player_sequence[game.board.state.player_counter]	
	game.board.state.active_player = active_player
	
	palabra_elegida = game.board.cartas.pop(0)
	game.board.state.acciones_carta_actual = palabra_elegida	
	
	save(bot, game.cid)
	bot.send_message(cid, game.board.print_board(game), ParseMode.MARKDOWN)
	game.dateinitvote = datetime.datetime.now()
	game.board.state.fase_actual = "Proponiendo Pistas"
	call_players_to_clue(bot, game)
	save(bot, game.cid)
	'''	
	game.dateinitvote = datetime.datetime.now()
	call_players_to_clue(bot, game)			
	game.dateinitvote = datetime.datetime.now()
	game.board.state.fase_actual = "Proponiendo Pistas"
	save(bot, game.cid)
	'''
# Actual
# start_round_say_anything -> call_players_to_clue -> Players /resp -> send_prop -> /pick N -> start_next_round
#  ------------------------"Proponiendo Pistas"------------------------------  --- Adivinando--

# Objetivo
# start_round_say_anything -> call_players_to_clue -> Players /resp -> send_prop -> /pick N (Pantalla secreta) -> call_players_to_vote -> Players Teclado para votar -> resolve_votes -> start_next_round
#  ------------------------"Proponiendo Pistas"-----------------------  ------------Adivinando-----------------  ------------------------Voting-------------------------------------

#  ------------------------"Proponiendo Pistas"-----------------------
def call_players_to_clue(bot, game):
	for uid in game.playerlist:
		if uid != game.board.state.active_player.uid:
			#bot.send_message(cid, "Enviando mensaje a: %s" % game.playerlist[uid].name)
			mensaje = "Nueva frase en el grupo *{1}*.\nEl jugado activo es: *{2}*\nLa frase es: *{0}*, propone tu respuesta!".format(
				game.board.state.acciones_carta_actual, game.groupName, game.board.state.active_player.name)
			bot.send_message(uid, mensaje, ParseMode.MARKDOWN)
			mensaje = "/resp Ejemplo" if game.board.num_players != 3 else "/resp Ejemplo Ejemplo2"
			bot.send_message(uid, mensaje)

#------------Adivinando -> Eligiendo----------------- 
def send_prop(bot, game):	
	mensaje = get_respuestas(bot, game)
	game.board.state.fase_actual = "Adivinando"
	save(bot, game.cid)	
	bot.send_message(game.cid, mensaje, ParseMode.MARKDOWN)
	# Comentar cuando este en produccion
	call_players_to_vote(bot, game)
	bot.send_message(game.cid, "El resto de jugadores puede comenzar a votar!")

def get_respuestas(bot, game):
	text = ""
	i = 1
	
	for vote in game.board.state.ordered_votes:		
		text += "*{1}: {0}*\n".format(vote.content['propuesta'], i)
		i += 1		
	respuestas = "Las respuestas son:\n{}".format(text)
	return "{0} es hora de elegir! Elige con /pick NUMERO (En privado)\n*{1}*\n{2}\n".format(
		player_call(game.board.state.active_player), game.board.state.acciones_carta_actual, respuestas)		

# Jugador activo hace /pick en secreto

def call_players_to_vote(bot, game):
	save(bot, game.cid)
	if not hasattr(game.board.state, 'votes_on_votes'):
		game.board.state.votes_on_votes = []
	for uid in game.playerlist:
		if uid != game.board.state.active_player.uid:					
			send_vote_buttons(bot, game, uid)			

def send_vote_buttons(bot, game, uid, message_id = None):
	mensaje = "Debes votar sobre las respuestas en el grupo *{1}*.\nEl jugado activo es: *{2}*\nLa frase es: *{0}*".format(
		game.board.state.acciones_carta_actual, game.groupName, game.board.state.active_player.name)
			
	opciones_botones = { }
	i = 0
	for vote in game.board.state.ordered_votes:
		votos_a_respuesta = [(val[0], val[1], val[2]) for index, val in enumerate(game.board.state.votes_on_votes) if val[2]==i]
		jugadores_votos_a_respuesta = "".join(("({})".format(o[0].name[:2])) for o in votos_a_respuesta)
		jugadores_votos_a_respuesta = jugadores_votos_a_respuesta if len(jugadores_votos_a_respuesta) < 24 else jugadores_votos_a_respuesta[:20] + '...'
		opciones_botones[i] = "{0} {1}".format(jugadores_votos_a_respuesta, vote.content['propuesta'])
		i += 1
	opciones_botones[-1] = "Terminar"
	btnMarkup = simple_choose_buttons_only_buttons(bot, game.cid, uid, "voteRespuestaSA", opciones_botones)
	
	if message_id:
		bot.edit_message_text("{0}\n*Ingresa/Modifica* tus votos".format(mensaje), chat_id=uid, message_id=message_id, 
				      parse_mode=ParseMode.MARKDOWN, reply_markup=btnMarkup)
	else:
		bot.send_message(uid, "{0}*Ingresa/Modifica* tus votos".format(mensaje), parse_mode=ParseMode.MARKDOWN, reply_markup=btnMarkup)
	
def callback_put_vote(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_put_vote called')
	callback = update.callback_query
	try:		
		#log.info('callback_finish_game_buttons called: %s' % callback.data)	
		regex = re.search("(-[0-9]*)\*voteRespuestaSA\*(.*)\*([0-9]*)", callback.data)
		cid, strcid, opcion, uid, struid = int(regex.group(1)), regex.group(1), regex.group(2), int(regex.group(3)), regex.group(3)
		game = get_game(cid)
		
		# Si alguien quiere votar antes de tiempo o el jugador activo quiere hacerlo...
		if game.board.state.fase_actual == "Proponiendo Pistas" or uid == game.board.state.active_player.uid:
			bot.edit_message_text("*No es momento de votar!*", chat_id=uid, message_id=callback.message.message_id, 
					      parse_mode=ParseMode.MARKDOWN)
		# Si decidio terminar le doy las gracias y continuo.
		if not hasattr(game.board.state, 'votes_on_votes'):
			game.board.state.votes_on_votes = []
		# Tuplas de votos (UID=de quien es el voto, PUNTAJE=valor del voto, INDEX_ORDERED_VOTES=respeusta que apunta)  
		lista_votos_usuario = [(index, val[2]) for index, val in enumerate(game.board.state.votes_on_votes) if val[0].uid==uid]
		
		if opcion == "-1":
			if game.board.state.fase_actual != "Votando Frases" or len(lista_votos_usuario) == 2:
				bot.edit_message_text("*Muchas Gracias!*", chat_id=uid, 
						      message_id=callback.message.message_id, parse_mode=ParseMode.MARKDOWN)
			else:
				bot.send_message(uid, "Debes ingresar al tus *2 votos*", parse_mode=ParseMode.MARKDOWN)
			return
		
		# Si ya voto dos veces quito el indice mas bajo de sus votos y agrego el nuevo
		if len(lista_votos_usuario) == 2:
			# Borro el elemento ingresado mas viejo
			index_to_remove = lista_votos_usuario[0][0]
			del game.board.state.votes_on_votes[index_to_remove]		
		player = game.playerlist[uid]
		game.board.state.votes_on_votes.append((player, 1, int(opcion)))		
		save(bot, game.cid)		
		send_vote_buttons(bot, game, uid, message_id = callback.message.message_id)
		# Si ya todos hicieron sus 2 votos (menos el jugador activo) cuento puntos
		if (len(game.board.state.votes_on_votes) == (len(game.player_sequence)-1)*2) and game.board.state.index_pick_resp != -1:
			count_points(bot, game)		
	except Exception as e:
		aux = ""
		# Se comenta ya que el error que tira es cuando se manda a edit y no se ha modificado nada. 
		#bot.send_message(ADMIN[0], 'No se ejecuto el comando debido a: '+str(e))
		#bot.send_message(ADMIN[0], callback.data)	      

def count_points(bot, game):
	'''
	frase_elegida = game.board.state.ordered_votes[game.board.state.index_pick_resp]	
	jugador_favorecido = frase_elegida.player
	
	mensaje = "La frase elegida fue: *{0}* de {1}! El cual gana 1 punto!".format(frase_elegida.content['propuesta'], player_call(jugador_favorecido))
	jugador_favorecido.puntaje += 1
	
	votos_a_respuesta_elegida = [(val[0], val[1], val[2]) for index, val in enumerate(game.board.state.votes_on_votes) if val[2]==game.board.state.index_pick_resp]
	mensaje += "\nA su vez los jugadores que votaron la frase:\n" if len(votos_a_respuesta_elegida) else "\nNingun jugador voto la frase"
	votos_dif_jugadores = []
	
	for voto in votos_a_respuesta_elegida:
		player = voto[0]
		player.puntaje += voto[1]
		if player.uid not in votos_dif_jugadores and len(votos_dif_jugadores) < 3:
			votos_dif_jugadores.append(player.uid)		
		mensaje += "{name} gano {puntos} punto\n".format(name=player.name, puntos=voto[1])
	game.board.state.active_player.puntaje += len(votos_dif_jugadores)	
	
	mensaje += "El jugador activo ha ganado *{}* por los votos de diferentes jugadores (MAX 3)".format(len(votos_dif_jugadores)) if len(votos_dif_jugadores) > 0 else ""	
	bot.send_message(game.cid, mensaje, ParseMode.MARKDOWN)
	#save(bot, game.cid)
	start_next_round(bot, game)
	'''
	frase_elegida = game.board.state.ordered_votes[game.board.state.index_pick_resp]	
	jugador_favorecido = frase_elegida.player
	
	mensaje = "La frase elegida fue: *{0}* de {1}! El cual gana 1 punto!".format(frase_elegida.content['propuesta'], 
										     player_call(jugador_favorecido))
	bot.send_message(game.cid, mensaje, ParseMode.MARKDOWN)
	jugador_favorecido.puntaje += 1
	
	votos_a_respuesta_elegida = [(val[0], val[1], val[2]) for index, val in enumerate(game.board.state.votes_on_votes) 
				     if val[2]==game.board.state.index_pick_resp]
	mensaje = "A su vez los jugadores que votaron la frase:\n"
	votos_dif_jugadores = []
	
	for voto in votos_a_respuesta_elegida:
		player = voto[0]
		player.puntaje += voto[1]
		if player.uid not in votos_dif_jugadores and len(votos_dif_jugadores) < 3:
			votos_dif_jugadores.append(player.uid)
		
		mensaje += "{name} gano {puntos} punto\n".format(name=player.name, puntos=voto[1])
	game.board.state.active_player.puntaje += len(votos_dif_jugadores)
	bot.send_message(game.cid, "El jugador activo ha ganado *{}* por los votos de diferentes jugadores (MAX 3)".format(
		len(votos_dif_jugadores)), ParseMode.MARKDOWN)
	bot.send_message(game.cid, mensaje, ParseMode.MARKDOWN)
	#save(bot, game.cid)
	start_next_round(bot, game)
		
def pass_say_anything(bot, game):
	bot.send_message(game.cid, "La frase era: *{0}*. El jugador activo no le gusto ninguna respuesta.".format(
		game.board.state.acciones_carta_actual), ParseMode.MARKDOWN)
	start_next_round(bot, game)

def start_next_round(bot, game):
	log.info('Verifing End_Game called')
	if not game.board.cartas:
		# Si no quedan cartas se termina el juego y se muestra el puntaje.
		mensaje = "Juego finalizado!:\n*{0}*".format(game.board.print_puntaje(game))		
		game.board.state.fase_actual = "Finalizado"
		save(bot, game.cid)
		bot.send_message(game.cid, mensaje, ParseMode.MARKDOWN)
		continue_playing(bot, game)
		#bot.send_message(game.cid, "Para comenzar un juego nuevo pon el comando /delete y luego /newgame", ParseMode.MARKDOWN)
		return
	increment_player_counter(game)
	start_round_say_anything(bot, game)

def continue_playing(bot, game):
	opciones_botones = { "Nuevo" : "(Beta) Nuevo Partido", 
			    "Mismo Diccionario" : "(Beta) Nuevo Partido, mismos jugadores, mismo diccionario", 
			    "Otro Diccionario" : "(Beta) Nuevo Partido, mismos jugadores, diferente diccionario"}
	simple_choose_buttons(bot, game.cid, 1, game.cid, "chooseendSA", "¿Quieres continuar jugando?", opciones_botones)
	
def callback_finish_game_buttons(update: Update, context: CallbackContext):
	bot = context.bot
	callback = update.callback_query
	try:		
		#log.info('callback_finish_game_buttons called: %s' % callback.data)	
		regex = re.search("(-[0-9]*)\*chooseendSA\*(.*)\*([0-9]*)", callback.data)
		cid, strcid, opcion, uid, struid = int(regex.group(1)), regex.group(1), regex.group(2), int(regex.group(3)), regex.group(3)
		mensaje_edit = "Has elegido el diccionario: {0}".format(opcion)
		try:
			bot.edit_message_text(mensaje_edit, cid, callback.message.message_id)
		except Exception as e:
			bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)				
		game = get_game(cid)
		
		# Obtengo el diccionario actual, primero casos no tendre el config y pondre el community
		try:
			dicc = game.configs.get('diccionario','community')
		except Exception as e:
			dicc = 'community'
		
		# Obtengo datos de juego anterior		
		groupName = game.groupName
		tipojuego = game.tipo
		modo = game.modo
		descarte = game.board.discards
		# Dependiendo de la opcion veo que como lo inicio
		players = game.playerlist.copy()
		# Creo nuevo juego
		game = Game(cid, uid, groupName, tipojuego, modo)
		GamesController.games[cid] = game
		# Guarda los descartes en configs para asi puedo recuperarlos
		game.configs['discards'] = descarte
		if opcion == "Nuevo":
			bot.send_message(cid, "Cada jugador puede unirse al juego con el comando " + 
					 "/join.\nEl iniciador del juego (o el administrador) pueden unirse tambien"+
					 "y escribir /startgame cuando todos se hayan unido al juego!")			
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
			finish_config(bot, game, dicc)
		if opcion == "Otro Diccionario":
			#(Beta) Nuevo Partido, mismos jugadores, diferente diccionario
			call_dicc_buttons(bot, game)				
	except Exception as e:
		bot.send_message(ADMIN[0], 'No se ejecuto el comando debido a: '+str(e))
		bot.send_message(ADMIN[0], callback.data)

def myturn_message(game, uid):
	try:
		group_link_name = "[{0}]({1})".format(game.groupName, get_config_data(game, "link"))
		#group_link_name = game.groupName if get_config_data(game, "link")==None else "[{0}]({1})".format(game.groupName, get_config_data(game, "link"))
		#	group_link_name = "[{0}]({1})".format(game.groupName, get_config_data(game, "link"))
		# Verifico en mi maquina de estados que comando deberia usar para el estado(fase) actual
		if game.board.state.fase_actual == "Proponiendo Pistas":
			return "Partida: {} debes dar {} para la palabra: *{}*.\nAdivina el jugador *{}*".format(
				group_link_name, player_call(game.playerlist[uid]), game.board.state.acciones_carta_actual, 
				game.board.state.active_player.name)
		elif game.board.state.fase_actual == "Revisando Pistas":
			return "Partida: {} Revisor recorda que tenes que verificar las pistas".format(group_link_name)
		elif game.board.state.fase_actual == "Adivinando":
			log.info("My Turn message: Fase: {} Grupo {}".format(game.board.state.fase_actual, game.groupName))
			return "Partida: {} estamos esperando para que hagas /guess EJEMPLO o /pass".format(group_link_name)
	except Exception as e:
		return str(e)