#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Eduardo Peluffo"

import copy
import json
import logging as log
import re
from random import randrange, choice, shuffle
from time import sleep
import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update, InputMediaPhoto
from telegram.ext import (Updater, CommandHandler, CallbackQueryHandler, CallbackContext)

from Utils import get_game, save, simple_choose_buttons
from Constants.Config import ADMIN



from Wavelength.Constants.Config import RIGHTLEFT, CHANGEGRADE, CONFIRMRESTART

from Wavelength.Boardgamebox.Game import Game
from Wavelength.Boardgamebox.Player import Player
from Wavelength.Boardgamebox.Board import Board

from Utils import player_call

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
	log.info('wavelength init called')
	game.shuffle_player_sequence()
	game.create_teams(2)
	start_round(bot, game)

# Objetivo
# start_round/send_wavelength -> Set reference -> send_ref ->  send_guess/resolve/start_next_round
#  ---------------Set_Reference----------------   Predict  ---   Predict_Opp_LR  -------------------

def start_round(bot, game):
	log.info('start_round_Wave called')
	cid = game.cid
	# The board gets a new wave card
	# TODO Remove when all game are new
	try:
		game.turncount += 1
	except AttributeError:
		game.turncount = 1
	if game.suddenDeath >= 0:
		game.suddenDeath += 1
	game.board.state.fase_actual = "Set_Reference"
	game.board.new_wave_card()
	send_wavelength(bot, game)


def send_wavelength(bot, game):
	game.board.print_board(bot, game)
	msg = "{} tienes que poner una referencia!".format(player_call(game.board.state.active_team.active_player))
	bot.send_message(game.cid, msg, ParseMode.MARKDOWN)
	active_wave_card = game.board.state.active_wave_card
	call_other_players = ""
	for player in game.board.state.active_team.player_sequence:
		call_other_players += "{} ".format(player_call(player)) if player.uid != game.board.state.active_team.active_player.uid else ""

	msg = "Partida en el grupo *{}* con tus compañeros {}\n\nLa carta que te ha tocado es: *{}*/*{}*.\nPone tu pista con /ref EJEMPLO EJEMPLO".format(
		game.groupName, call_other_players, active_wave_card["Izquierda"], active_wave_card["Derecha"])
	bot.send_message(game.board.state.active_team.active_player.uid, msg, ParseMode.MARKDOWN)
	bio = "https://ssl.hq063.com.ar/pbt/imagen.php?angle={}&size=th&text={}|{}&v=201903131425".format(game.board.state.wavelength, active_wave_card["Izquierda"], active_wave_card["Derecha"])
	bot.send_photo(game.board.state.active_team.active_player.uid, photo=bio, caption="{}-----------------------{}".format(active_wave_card["Izquierda"], active_wave_card["Derecha"]))
	save(bot, game.cid)

#Active player send reference of wavelength
def send_ref(bot, game):
	game.board.print_board(bot, game)
	active_wave_card = game.board.state.active_wave_card
	call_other_players = ""
	for player in game.board.state.active_team.player_sequence:
		call_other_players += "{} ".format(player_call(player)) if player.uid != game.board.state.active_team.active_player.uid else ""
	msg = "La referencia es:\n*{}*. {}les toca adivinar!".format(game.board.state.reference, call_other_players)
	bot.send_message(game.cid, msg, ParseMode.MARKDOWN)
	game.board.state.fase_actual = "Predict"
	save(bot, game.cid)
	game.board.state.team_choosen_grade = 90
	draw_choose_needle(bot, game)

#Draws the picture and the needle so the team can select it.
def draw_choose_needle(bot, game, message_id = None):
	cid = game.cid
	active_wave_card = game.board.state.active_wave_card
	needle = "&needle={}".format(game.board.state.team_choosen_grade)
	bio = "https://ssl.hq063.com.ar/pbt/imagen.php?size=th{}&text={}|{}&v={}".format(needle, active_wave_card["Izquierda"], active_wave_card["Derecha"], datetime.datetime.now().strftime("%Y%m%d%H"))
	btnMarkup = create_choose_buttons2(cid, "ChangeGradeWave", CHANGEGRADE, CONFIRMRESTART)
	# Re draw if previous
	call_other_players = ""
	for player in game.board.state.active_team.player_sequence:
		call_other_players += "{} ".format(player_call(player)) if player.uid != game.board.state.active_team.active_player.uid else ""
	caption = "{}-----------------------{}\n\nLa referencia es: *{}*\nDecidan: {}".format(active_wave_card["Izquierda"], active_wave_card["Derecha"], game.board.state.reference, call_other_players)

	log.info(bio)

	if message_id:
		#bot.delete_message(chat_id=cid, message_id=message_id)
		bioInputMedia = InputMediaPhoto(media=bio,
						caption=caption,
						parse_mode=ParseMode.MARKDOWN)
		#InputMediaPhoto(media=TestInputMediaPhoto.media, caption=TestInputMediaPhoto.caption, parse_mode=TestInputMediaPhoto.parse_mode)
		bot.edit_message_media(chat_id=cid,
				       message_id=message_id,
				       media=bioInputMedia,
				       reply_markup=btnMarkup)
	# Draw again
	else:
		bot.send_photo(cid, photo=bio,
			       reply_markup=btnMarkup,
			       parse_mode=ParseMode.MARKDOWN,
			       caption=caption)
	save(bot, game.cid)

def send_guess(bot, game):
	# To improve game pace, we eagerly check if there is a bullseye and prevent
	# the other team from having to do an useless left/right guess
	diff = abs(game.board.state.wavelength - game.board.state.team_choosen_grade)
	if diff < 3:
		resolve(bot, game)
		return

	game.board.print_board(bot, game)
	active_wave_card = game.board.state.active_wave_card
	call_other_players = ""
	for player in game.board.state.inactive_team.player_sequence:
		call_other_players += "{} ".format(player_call(player))
	msg = "La referencia dada fue:\n*{}*\n\nEquipo contrario {} elija si la respuesta correcta esta a la izquierda o derecha.".format(game.board.state.reference, call_other_players)
	bot.send_message(game.cid, msg, ParseMode.MARKDOWN)
	game.board.state.fase_actual = "Predict_Opp_LR"
	save(bot, game.cid)
	bio = "https://ssl.hq063.com.ar/pbt/imagen.php?needle={}&size=th&text={}|{}&v={}".format(game.board.state.team_choosen_grade, active_wave_card["Izquierda"], active_wave_card["Derecha"], datetime.datetime.now().strftime("%Y%m%d"))
	btnMarkup = create_choose_buttons(game.cid, "LeftRightWave", RIGHTLEFT, True)
	bot.send_photo(game.cid, photo=bio, reply_markup=btnMarkup,
		       parse_mode=ParseMode.MARKDOWN,
		       caption="{}-----------------------{}\n\nLa referencia es: *{}*".format(
			       active_wave_card["Izquierda"],
			       active_wave_card["Derecha"],
			       game.board.state.reference))
	save(bot, game.cid)

def resolve(bot, game, args = []):
	log.info('resolve_Wave called')
	# Resolvemos
	catchup_rule = False
	active_wave_card = game.board.state.active_wave_card
	diff = game.board.state.wavelength - game.board.state.team_choosen_grade
	abs_diff = abs(diff)
	textCache = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
	bio = "https://ssl.hq063.com.ar/pbt/imagen.php?needle={}&angle={}&size=th&text={}|{}&v={}".format(game.board.state.team_choosen_grade, game.board.state.wavelength, active_wave_card["Izquierda"], active_wave_card["Derecha"], textCache)
	log.info(bio)
	bot.send_photo(game.cid, photo=bio, caption="{}-----------------------{}".format(active_wave_card["Izquierda"], active_wave_card["Derecha"]))
	msg = "La carta que ha tocado es:\n*{}*------------*{}*.\n\nLa referencia dada fue: *{}*.\n\nEl equipo contrario dijo que estaba: *{}*\n".format(
		active_wave_card["Izquierda"],
		active_wave_card["Derecha"],
		game.board.state.reference,
		"a la Izquierda" if game.board.state.opponent_team_choosen_left_right == 0 else "a la Derecha")
	if abs_diff <= 3:
		game.board.state.active_team.score += 4
		msg += "\n*BULLSEYE!!!! 4 PUNTOS!!!*"
	elif abs_diff <= 9:
		game.board.state.active_team.score += 3
		msg += "\nEl equipo activo ha adivinado en la franja verde, ha ganado *3 puntos*!"
	elif abs_diff <= 15:
		game.board.state.active_team.score += 2
		msg += "\nEl equipo activo ha adivinado en la franja marrón, ha ganado *2 punto*!"
	opp_choose_l_r = game.board.state.opponent_team_choosen_left_right
	if ((diff > 0 and opp_choose_l_r == 1) or (diff < 0 and opp_choose_l_r == 0)) and abs_diff > 3:
		game.board.state.inactive_team.score += 1
		msg += "\nEl equipo inactivo ha correctamente si estaba a la derecha o izquierda del bulls eye. Ha ganado *1 punto*!"

	if game.board.state.active_team.score < game.board.state.active_team.score:
		msg += "\n\nEl equipo activo ha hecho bullseye y sigue teniendo menor puntaje, se activa la regla de compensación."
		msg += "\nEl equipo activo tiene otro turno."
		catchup_rule = True

	bot.send_message(game.cid, msg, ParseMode.MARKDOWN)
	msg = "*(Debug data)*\nEl grado elegido es *{}*\nEl equipo contrario eligio *{}*.\n\nEl grado real era *{}*".format(
		game.board.state.team_choosen_grade,
		"a la Izquierda" if game.board.state.opponent_team_choosen_left_right == 0 else "a la Derecha",
		game.board.state.wavelength)
	game.history.append(msg)
	start_next_round(bot, game, catchup_rule)

def start_next_round(bot, game, catchup_rule):
	# Verifico si alguno de los dos equipos ha llegado a los puntos para ganar.
	# O si estan en muerte subita y jugaron una vez cada equipo
	if (game.board.state.active_team.score >= 10
	    or game.board.state.inactive_team.score >= 10) or (
		game.suddenDeath == 2):

		game.board.print_board(bot, game)

		# El juego ha terminado!
		team_diff = game.board.state.active_team.score - game.board.state.inactive_team.score
		if team_diff > 0:
			bot.send_message(game.cid, "El equipo: *{}* HA GANADO!".format(
				game.board.state.active_team.name), ParseMode.MARKDOWN)
		elif team_diff < 0:
			bot.send_message(game.cid, "El equipo: *{}* HA GANADO!".format(
				game.board.state.inactive_team.name), ParseMode.MARKDOWN)
		elif team_diff == 0:
			bot.send_message(game.cid, "El juego esta empatado! *MUERTE SUBITA!*", ParseMode.MARKDOWN)
			game.suddenDeath = 0 # immediately after start_round will add 1
			game.board.state.increment_team_counter()
			start_round(bot, game)
			return
		game.board.state.fase_actual = "Finalizado"
		save(bot, game.cid)
	else:
		# El juego continua
		if catchup_rule == True:
			game.board.state.increment_player_counter()
		else:
			game.board.state.increment_team_counter()
		start_round(bot, game)

def continue_playing(bot, game):
	opciones_botones = { "Nuevo" : "Cambiar jugadores", "Mantener" : "Mismos jugadores" }
	simple_choose_buttons(bot, game.cid, 1, game.cid, "chooseendWL", "¿Quieres continuar jugando?", opciones_botones)

def callback_finish_game_buttons(update: Update, context: CallbackContext):
	bot = context.bot
	callback = update.callback_query
	try:
		#log.info('callback_finish_game_buttons called: %s' % callback.data)
		regex = re.search(r"(-[0-9]*)\*chooseendWL\*(.*)\*([0-9]*)", callback.data)
		cid, opcion, uid  = int(regex.group(1)), regex.group(2), int(regex.group(3))
		mensaje_edit = "Has elegido: {0}".format(opcion)
		try:
			bot.edit_message_text(mensaje_edit, cid, callback.message.message_id)
		except Exception as e:
			bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)
		game = get_game(cid)

		# Obtengo el diccionario actual, primero casos no tendre el config y pondre el community
		try:
			diff = game.configs.get('difficultad', 0)
		except Exception as e:
			diff = 0

		# Obtengo datos de juego anterior
		groupName = game.groupName
		tipojuego = game.tipo
		modo = game.modo

		# Dependiendo de la opcion veo que como lo inicio

		players = game.playerlist.copy()

		# Creo nuevo juego
		game = Game(cid, uid, groupName, tipojuego, modo)
		GamesController.games[cid] = game

		if opcion == "Nuevo":
			bot.send_message(cid, "Cada jugador puede unirse al juego con el comando /join.\nEl iniciador del juego (o el administrador) pueden unirse tambien y escribir /startgame cuando todos se hayan unido al juego!")
			return

		# Si no es nuevo entonces los jugadores son agregados y los equipos crados
		for uid in players:
			game.add_player(uid, players[uid].name)
		# StartGame
		player_number = len(game.playerlist)
		game.board = Board(player_number, game)
		game.player_sequence = []

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
