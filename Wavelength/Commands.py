import json
import logging as log
import datetime
#import ast
import jsonpickle
import os
import psycopg2
import urllib.parse
import sys
from time import sleep

import Wavelength.Controller as WavelengthController
from Utils import get_game, save

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update, ForceReply, Update
from telegram.ext import (CallbackContext)
import MainController
from Constants.Config import STATS, ADMIN
from SayAnything.Boardgamebox.Board import Board
from SayAnything.Boardgamebox.Game import Game
from SayAnything.Boardgamebox.Player import Player
from Boardgamebox.State import State



from collections import namedtuple

from PIL import Image
from io import BytesIO

# Objetos que uso de prueba estaran en el state
from Constants.Cards import cartas_aventura
from Constants.Cards import opciones_opcional
from Constants.Cards import opciones_choose_posible_role
from Constants.Cards import modos_juego

from Constants.Config import JUEGOS_DISPONIBLES
from Constants.Config import MODULOS_DISPONIBES
from Constants.Config import HOJAS_AYUDA

from Wavelength.Constants.Config import RIGHTLEFT, CHANGEGRADE, CONFIRMRESTART

from Constants.Cards import comandos
import random
import re
# Objetos que uso de prueba estaran en el state

# Enable logging

log.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=log.INFO)
logger = log.getLogger(__name__)

def command_pass(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	uid = update.message.from_user.id
	game = get_game(cid)
	# Solo el active player puede pasar y pedir nueva carta
	if uid == game.board.state.active_team.active_player.uid and game.board.state.fase_actual == "Set_Reference":
		active_wave_card = game.board.state.active_wave_card
		bot.send_message(game.cid, "{} decidio descartar la carta {}/{}. Se le enviara nueva carta.".format(
			game.board.state.active_team.active_player.name, 
			active_wave_card["Izquierda"], 
			active_wave_card["Derecha"]))
		game.board.new_wave_card()
		WavelengthController.send_wavelength(bot, game)		
	
def command_call(bot, game):
	import Wavelength.Controller as WavelengthController
	
	try:		
	# Verifico en mi maquina de estados que comando deberia usar para el estado(fase) actual
		if game.board.state.fase_actual == "Set_Reference":
			WavelengthController.send_wavelength(bot, game)
		elif game.board.state.fase_actual == "Predict":
			WavelengthController.draw_choose_needle(bot, game)
		elif game.board.state.fase_actual == "Predict_Opp_LR":
			WavelengthController.send_guess(bot, game)
	except Exception as e:
		bot.send_message(game.cid, str(e))

def command_draw(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	cid = update.message.chat_id
	uid = update.message.from_user.id
	
	if len(args) < 1:
		game = get_game(cid)
		WavelengthController.draw_choose_needle(bot, game)
	else:
		needle = "" if args[0] =="-1" else "&needle="+args[0]
		angle = "" if args[1] =="-1" else "&angle="+args[1]
		bio = "https://ssl.hq063.com.ar/pbt/imagen.php?size=th{}{}&text=Frio|Calor".format(needle, angle)
		btnMarkup = create_choose_buttons2(cid, "ChangeGradeWave", CHANGEGRADE, CONFIRMRESTART)
		bot.send_photo(cid, photo=bio, reply_markup=btnMarkup, caption="Frio---------------------------Calor")
	
# Callback general para Wavelength
def callback_Wave(update: Update, context: CallbackContext):
	bot = context.bot
	callback = update.callback_query
	log.info('callback_Wave called: %s' % callback.data)
	regex = re.search("(-?[0-9]*)\*([A-Za-z]*)Wave\*(.*)\*(.*)", callback.data)
	uid = update.effective_user.id
	cid, strcid, accion, dato1, dato2 = int(regex.group(1)), regex.group(1), regex.group(2), regex.group(3), regex.group(4)
	game = get_game(cid)
	
	log.info("Accion: {} Data: {} {}. Fase actual {}".format(accion, dato1, dato2, game.board.state.fase_actual))
	# Left Right action, Predict_Opp_LR phase, belongs to inactive team.
	if accion == "LeftRight" and game.board.state.fase_actual == "Predict_Opp_LR" and (game.board.state.inactive_team.belongs(uid) or uid == ADMIN[0]):
		command_left_right(bot, [dato1, cid, uid])
	# Change Grade action, predict phase, belong to active team, and not the active player.	
	elif accion == "ChangeGrade" and game.board.state.fase_actual == "Predict" and ((game.board.state.active_team.belongs(uid) and game.board.state.active_team.active_player.uid != uid ) or uid == ADMIN[0]):
		refresh = False
		if dato1 == "0":
			game.board.state.team_choosen_grade = 0
			refresh = True
		elif dato1 == "-10":
			game.board.state.team_choosen_grade -= 10
			refresh = True
		elif dato1 == "-1":
			game.board.state.team_choosen_grade -= 1
			refresh = True
		elif dato1 == "1":
			game.board.state.team_choosen_grade += 1
			refresh = True
		elif dato1 == "10":
			game.board.state.team_choosen_grade += 10
			refresh = True
		elif dato1 == "180":
			game.board.state.team_choosen_grade = 180
			refresh = True
		elif dato1 == "refresh":
			refresh = True
		elif dato1 == "restart":
			game.board.state.team_choosen_grade = 90
			refresh = True
		elif dato1 == "confirm":
			command_pick(bot, update, ["{}".format(game.board.state.team_choosen_grade), cid, uid])
			bot.delete_message(chat_id=cid, message_id=callback.message.message_id)
			return
		
		if game.board.state.team_choosen_grade > 180:
			game.board.state.team_choosen_grade = 180
		if game.board.state.team_choosen_grade < 0:
			game.board.state.team_choosen_grade = 0	
		
		# If not confirm, then check if we have to refresh
		if refresh:
			WavelengthController.draw_choose_needle(bot, game, callback.message.message_id)
		
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
	


def callback_choose_game_prop(update: Update, context: CallbackContext):
	bot = context.bot
	user_data = context.user_data
	callback = update.callback_query
	log.info('callback_choose_game_prop called: %s' % callback.data)	
	regex = re.search("(-[0-9]*)\*choosegamerefWL\*(.*)\*([0-9]*)", callback.data)
	cid, strcid, opcion, uid, struid = int(regex.group(1)), regex.group(1), regex.group(2), int(regex.group(3)), regex.group(3)	
	
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
		if uid == ADMIN[0] or (uid == game.board.state.active_team.active_player.uid):
			bot.send_message(uid, "Tu referencia: {} fue agregada.".format(propuesta))			
			game.board.state.reference = propuesta			
			save(bot, game.cid)
			WavelengthController.send_ref(bot, game)			
		else:
			bot.send_message(uid, "No puedes poner referencia si NO sos el jugador activo o no es la fase correcta")
	else:
		bot.send_message(uid, "No puedes hacer ref si no estas en el partido.")
		
# Por defecto no hay restricciones
def get_choose_game_buttons(games_tipo, uid, fase_actual, button_value, callback_command):	
	btns = []
	cid = None
	for game_chat_id, game in games_tipo.items():
		if uid in game.playerlist and game.board != None:
			log.info('uid: {} active player uid {}, fase actual {}'.format(uid, game.board.state.active_team.active_player.uid,fase_actual))
			allow_only_id = game.board.state.active_team.active_player.uid
			if uid == allow_only_id and game.board.state.fase_actual == fase_actual:
				clue_text = button_value
				# Pongo en cid el id del juego actual, para el caso de que haya solo 1
				cid = game_chat_id
				# Creo el boton el cual eligirá el jugador
				txtBoton = game.groupName
				comando_callback = callback_command
				datos = str(game_chat_id) + "*" + comando_callback + "*" + clue_text + "*" + str(uid)
				btns.append([InlineKeyboardButton(txtBoton, callback_data=datos)])
	return btns, cid

def command_pick(bot, update, args):	
	try:
		cid, uid = update.message.chat_id, update.message.from_user.id
	except Exception as e:
		cid, uid = args[1], args[2]
	#log.info(args)	
	game = get_game(cid)
	
	if(check_valid_pick(args, 0, 180)):
		game.board.state.team_choosen_grade = int(args[0])
		save(bot, game.cid)
		WavelengthController.send_guess(bot, game)
	else:
		bot.send_message(uid, "El grado elegido ({}) es invalido (NO pasara con botonera)".format(args[0]))

def command_left_right(bot, args):
	cid, uid = args[1], args[2]
		
	game = get_game(cid)
	
	if(check_valid_pick(args, 0, 1)):
		game.board.state.opponent_team_choosen_left_right = int(args[0])
		save(bot, game.cid)
		WavelengthController.resolve(bot, game)
	else:
		bot.send_message(uid, "El grado elegido ({}) es invalido (NO pasara con botonera)".format(args[0]))
		
def check_valid_pick(args, min_value, max_calue):
	return (args[0].isdigit() and (min_value <= int(args[0]) <= max_calue))

def command_reference(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	user_data = context.user_data
	try:
		cid = update.message.chat_id
		uid = update.message.from_user.id
		if len(args) > 0:
			# Obtengo todos los juegos de base de datos de los que usan clue
			mensaje_error = ""			
			games_tipo = MainController.getGamesByTipo('Wavelength')						
			btns, cid = get_choose_game_buttons(games_tipo,
							    uid, 
							    fase_actual = 'Set_Reference',
							    button_value = 'prop',
							    callback_command = 'choosegamerefWL')
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
					bot.send_message(uid, "En cual de estos grupos queres mandar la referencia?", reply_markup=btnMarkup)
			else:
				mensaje_error = "No hay partidas en las que puedas hacer /ref"
				bot.send_message(uid, mensaje_error)
	except Exception as e:
		bot.send_message(uid, str(e))
		log.error("Unknown error: " + str(e))
