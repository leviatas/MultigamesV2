#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Eduardo Peluffo"

import copy
import logging as log
import re
from random import randrange, choice, shuffle
from time import sleep
import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update, ForceReply, Update
from telegram.ext import (Updater, CommandHandler, CallbackQueryHandler, CallbackContext)

from Utils import get_game, save
from Constants.Cards import playerSets, actions
from Constants.Config import TOKEN, STATS, ADMIN

from Decrypt.Boardgamebox.Game import Game
from Decrypt.Boardgamebox.Player import Player
from Decrypt.Boardgamebox.Board import Board
from Decrypt.Boardgamebox.Team import Team

from Utils import player_call, simple_choose_buttons

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
	log.info('Decrypt init called')	
	game.shuffle_player_sequence()
	game.create_teams(2)		
	call_dicc_buttons(bot, game)
	#start_round(bot, game)
	
def call_dicc_buttons(bot, game):
	#log.info('call_dicc_buttons called')
#	opciones_botones = { "original" : "Español Nuestro", "ficus" : "Español Ficus", "community" : "Español Community", "edespañola"  : "Original Ed Española"}
	opciones_botones = { "original" : "Español original", "community" : "Español Community"}
	simple_choose_buttons(bot, game.cid, 1234, game.cid, "choosediccDE", "¿Elija un diccionario para jugar?", opciones_botones)
		
def callback_finish_config_decrypt(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_finish_config_justone called')
	callback = update.callback_query
	try:
		regex = re.search("(-[0-9]*)\*choosediccDE\*(.*)\*([0-9]*)", callback.data)
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
	# Si vengo de un partido anterior agrego los descartes de la partida anterior.	
	if game.configs.get('discards', None):
		game.board.discards = game.configs.get('discards')
		del game.configs['discards']
	url_palabras_posibles = '/Decrypt/txt/spanish-{0}.txt'.format(opcion)	
	with open(url_palabras_posibles, 'r') as f:
		palabras_posibles = f.readlines()
		palabras_posibles_no_repetidas = list_menos_list(palabras_posibles, game.board.discards)
		# Si no hay palabra posible no repetidas para jugar mezclo todas las palabras posibles
		if len(palabras_posibles_no_repetidas) < 8:
			# Quedo bien 
			game.board.discards = []
			palabras_posibles_no_repetidas = palabras_posibles		
		shuffle(palabras_posibles_no_repetidas)		
		game.board.cards = palabras_posibles_no_repetidas[0:8]
		game.board.cards = [w.replace('\n', '') for w in game.board.cards]
		game.board.state.teams[0].cards = game.board.cards[0:4]
		game.board.state.teams[1].cards = game.board.cards[4:8]
	
	start_round(bot, game)
	
# Objetivo
# start_round/send_codes -> Set reference -> send_ref ->  send_guess/resolve/start_next_round
#  ---------------Set_Reference----------------   Predict  ---   Predict_Opp_LR  -------------------
	
def start_round(bot, game):
	log.info('start_round_Decrypt called')
	cid = game.cid
	
	game.turncount += 1
	game.board.state.fase_actual = "Set_Reference"
	# The board gets both teams a card to decrypt
	game.board.new_round(game)
	send_codes(bot, game)
	
def send_codes(bot, game):
	game.board.print_board(bot, game)
	msg = ''
	for player in [team.active_player for team in game.board.state.teams if team.clue == None]:
		msg += "{} tienes que escribir tu codigo!\n".format(player_call(player))
	bot.send_message(game.cid, msg, ParseMode.MARKDOWN)
	# Send codes to decrypters that dont send the clue
	for team in [team for team in game.board.state.teams if team.clue == None]:
		bot.send_message(team.active_player.uid, team.generate_code_message(game.groupName), ParseMode.MARKDOWN)
	save(bot, game.cid)

def inform_teams(bot, game):
	active_team = game.board.state.active_team
	inactive_team = game.board.state.inactive_team
	codigo_oponente = active_team.opponent_team_choosen_code
	codigo_equipo = active_team.team_choosen_code	
	
	if codigo_equipo is not None and ((codigo_oponente is not None) or game.turncount == 1):
		save(bot, game.cid)
		resolve(bot, game)
		return
	# imprimo el tablero
	if codigo_equipo is None and codigo_oponente is None:
		game.board.print_board(bot, game)	
	
	# Mando informacion a los interceptores si no hicieron su trabajo ya	
	
	if codigo_oponente is None and game.turncount != 1:		
		inactive_team.communicate_team(bot, inactive_team.generate_intercept_message(game.groupName, active_team.clue))
		call_other_players = inactive_team.generate_call_team_players()
		inactive_team.communicate_team(bot, game.board.state.active_team.printHistory())
		msg = "La referencia es:\n*{}*.\n{}les toca interceptar el codigo! /intercept ".format(active_team.clue, call_other_players)	
		bot.send_message(game.cid, msg, ParseMode.MARKDOWN)
		
	log.info("Paso por Intercept")
	# Mando informacion a los decriptores si no hicieron su trabajo ya
	if codigo_equipo is None:
		active_team.communicate_team(bot, active_team.generate_decrypt_message(game.groupName), exclude = [active_team.active_player.uid], messanger = "")		
		call_other_players = active_team.generate_call_team_players([active_team.active_player.uid])
		active_team.communicate_team(bot, active_team.printHistory(True), exclude = [active_team.active_player.uid], messanger = "")		
		msg = "La referencia es:\n*{}*.\n{}les toca desencriptar el codigo! /decrypt".format(active_team.clue, call_other_players)	
		bot.send_message(game.cid, msg, ParseMode.MARKDOWN)

	log.info("Paso por Intercept")
	# Mando historial a ambos equipos en el chat grupal si al menos alguno le falta hacer su trabajo
	if codigo_equipo is None and codigo_oponente is None and game.turncount != 1:
		bot.send_message(game.cid, active_team.printHistory(), ParseMode.MARKDOWN)
	# Si ambos equipos han terminado resuelvo.
	

def resolve(bot, game):	
	active_team = game.board.state.active_team
	code = active_team.code
	intercepcion = active_team.opponent_team_choosen_code
	desencriptacion = active_team.team_choosen_code
	
	log.info("Codigo correcto {} codigo elegido equipo {}".format(code, desencriptacion))	
	# Se revela si ha sido interceptado
	# if hasattr(game, 'verify_turn'):
	bot.send_message(game.cid, "El codigo correcto era: *{}*".format(code), ParseMode.MARKDOWN)
	
	if(game.turncount != 1):
		if (intercepcion == code):		
			game.board.state.inactive_team.interceptions += 1		
			bot.send_message(game.cid, "El equipo *{} ha interceptado* el mensaje!!!".format(game.board.state.inactive_team.name), ParseMode.MARKDOWN)
		else:
			bot.send_message(game.cid, "Incorrecto! {} no era el código. El equipo *{} NO ha interceptado* el mensaje!!!".format(intercepcion, game.board.state.inactive_team.name), ParseMode.MARKDOWN)	
	# Se revela si ha sido desencriptado
	if (desencriptacion == code):
		bot.send_message(game.cid, "El equipo *{} ha desencriptado* el codigo!!!".format(active_team.name), ParseMode.MARKDOWN)
	else:		
		active_team.miscommunications += 1
		bot.send_message(game.cid, "Incorrecto! {} no era el codigo! El equipo *{} NO ha desencriptado* el codigo!!!".format(desencriptacion, active_team.name), ParseMode.MARKDOWN)	
	
	active_team.saveHistory(active_team.clue, active_team.code)	
	
	if (desencriptacion != None and game.board.state.inactive_team.team_choosen_code != None):
		start_next_round(bot, game)
	else:
		game.board.state.swap_team()
		inform_teams(bot, game)
		save(bot, game.cid)

def verify_endgame(game):
	# Verifico si alguno de los dos equipos ha llegado a los puntos para ganar o perder.
	active_team_won = game.board.state.active_team.interceptions == 2
	inactive_team_won = game.board.state.inactive_team.interceptions == 2
	active_team_lose = game.board.state.active_team.miscommunications == 2
	inactive_team_lose = game.board.state.inactive_team.miscommunications == 2

	# Empate o ronda 8 terminada
	if((active_team_won and active_team_lose) or (inactive_team_won and inactive_team_lose) 
	   or (active_team_won and inactive_team_won) or (active_team_lose and inactive_team_lose) or game.turncount == 8):
		# Cuento los puntos y el que tenga mas puntos gana.
		white_team_points = game.board.state.teams[0].count_points(game.value_intercept, game.value_miscommunication, game.allow_half_guess, game.value_half_guess)
		black_team_points = game.board.state.teams[1].count_points(game.value_intercept, game.value_miscommunication, game.allow_half_guess, game.value_half_guess)
		if (white_team_points > black_team_points):
			return (1, game.board.state.teams[0])		
		elif (black_team_points > white_team_points):
			return (1, game.board.state.teams[1])
		else:
			return (None, "Intenten adivinar las palabras del otro equipo!!!")
	# Si solo uno gano lo anuncio.
	elif active_team_won or active_team_lose or inactive_team_won or inactive_team_lose:
		# Obtengo el ganador o perdedor
		if active_team_won or inactive_team_lose:
			return (1, game.board.state.active_team)
		else:
			return (1, game.board.state.inactive_team)
	else:
		return None


def start_next_round(bot, game):
	# Verifico si alguno de los dos equipos ha llegado a los puntos para ganar o perder.
	verify_end = verify_endgame(game)
	if verify_end:
		if verify_end[0]:
			palabras_team1 = "{}: *{}*".format(game.board.state.teams[0].name,  " ".join(game.board.state.teams[0].cards))
			palabras_team2 = "{}: *{}*".format(game.board.state.teams[1].name,  " ".join(game.board.state.teams[1].cards))
			bot.send_message(game.cid, "El equipo {} ha ganado!!!".format(verify_end[1].name), ParseMode.MARKDOWN)
			bot.send_message(game.cid, "Las palabras eran:\n\n{}\n\n{}!!!".format(palabras_team1, palabras_team2), ParseMode.MARKDOWN)
		else:
			print("{}".format(verify_end[1]))
		game.board.state.fase_actual = "Finalizado"
		save(bot, game.cid)
		continue_playing(bot, game)		
	else:
		# El juego continua se hace swap para que siempre empiece el mismo equiposwap_team
		game.board.state.swap_team()
		for team in game.board.state.teams:
			team.increment_player_counter()
		start_round(bot, game)

def continue_playing(bot, game):
	opciones_botones = { "Mismo Diccionario" : "Mismo Diccionario"}
	simple_choose_buttons(bot, game.cid, 1, game.cid, "chooseendDE", "¿Quieres continuar jugando?", opciones_botones)
	
def callback_finish_game_buttons(update: Update, context: CallbackContext):
	bot = context.bot
	callback = update.callback_query
	try:		
		log.info('callback_finish_game_buttons called: %s' % callback.data)	
		regex = re.search("(-[0-9]*)\*chooseendDE\*(.*)\*([0-9]*)", callback.data)
		cid, strcid, opcion, uid, struid = int(regex.group(1)), regex.group(1), regex.group(2), int(regex.group(3)), regex.group(3)
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
		# Dependiendo de la opcion veo que como lo inicio
		players = game.playerlist.copy()
		# Creo nuevo juego
		game = Game(cid, uid, groupName, tipojuego, modo)
		GamesController.games[cid] = game
		# Guarda los descartes en configs para asi puedo recuperarlos
		game.configs['discards'] = descarte
		if opcion == "Nuevo":
			bot.send_message(cid, "Cada jugador puede unirse al juego con el comando /join.\nEl iniciador del juego (o el administrador) pueden unirse tambien y escribir /startgame cuando todos se hayan unido al juego!")			
			return
		game.playerlist = players
		# StartGame
		player_number = len(game.playerlist)
		game.board = Board(player_number, game)		
		init_game(bot, game)
					
		    			
	except Exception as e:
		bot.send_message(ADMIN[0], 'No se ejecuto el comando debido a: '+str(e))
		bot.send_message(ADMIN[0], callback.data)

# Return two lines of buttons
def create_choose_buttons2(cid, accion, opciones_botones, opciones_botones2):
	#sleep(3)
	btnsResult = []
	btns = []
	btns2 = []
	# Creo los botones para elegir al usuario
	for key, value in opciones_botones.items():
		txtBoton = value
		datos = str(cid) + "*" + accion + "*" + str(key) + "*" + str(value)		
		btns.append(InlineKeyboardButton(txtBoton, callback_data=datos))
	btnsResult.append(btns)	
	
	for key, value in opciones_botones2.items():
		txtBoton = value
		datos = str(cid) + "*" + accion + "*" + str(key) + "*" + str(value)		
		btns2.append(InlineKeyboardButton(txtBoton, callback_data=datos))
	btnsResult.append(btns2)
	
	return InlineKeyboardMarkup(btnsResult)	
		
def create_choose_buttons(cid, accion, opciones_botones, one_line = True):
	#sleep(3)
	btns = []
	# Creo los botones para elegir al usuario
	for key, value in opciones_botones.items():
		txtBoton = value
		datos = str(cid) + "*" + accion + "*" + str(key) + "*" + str(value)		
		if one_line:
			btns.append(InlineKeyboardButton(txtBoton, callback_data=datos))
		else:
			btns.append([InlineKeyboardButton(txtBoton, callback_data=datos)])
	if one_line:
		return InlineKeyboardMarkup([btns])
	else:
		return InlineKeyboardMarkup(btns)
