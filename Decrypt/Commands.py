import json
import logging as log
import datetime
#import ast
import jsonpickle
import os
import psycopg
import urllib.parse
import sys
from time import sleep

import Decrypt.Controller as DecryptController
from Utils import get_game, save

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ForceReply
from telegram.constants import ParseMode
from telegram.ext import CallbackContext
import MainController
from Constants.Config import STATS
from Decrypt.Boardgamebox.Board import Board
from Decrypt.Boardgamebox.Game import Game
from Decrypt.Boardgamebox.Player import Player
from Boardgamebox.State import State

from Constants.Config import ADMIN

from Utils import player_call

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

from Constants.Cards import comandos
import random
import re
# Objetos que uso de prueba estaran en el state

# Enable logging

log.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=log.INFO)
logger = log.getLogger(__name__)

#DB Connection I made a Haroku Postgres database first
#urllib.parse.uses_netloc.append("postgres")
#url = urllib.parse.urlparse(os.environ["DATABASE_URL"])
#
#conn = psycopg.connect(
#    dbname=url.path[1:],
#    user=url.username,
#    password=url.password,
#    host=url.hostname,
#    port=url.port
#)
	
async def command_call(bot, game):	
	#try:		
	# Verifico en mi maquina de estados que comando deberia usar para el estado(fase) actual
	log.info("Call en {} fase {}".format(game.groupName, game.board.state.fase_actual))
	if game.board.state.fase_actual == "Intercept/Decrypt":
		await DecryptController.inform_teams(bot, game)
	if game.board.state.fase_actual == "Set_Reference":
		await DecryptController.send_codes(bot, game)	
	#except Exception as e:
	#	await bot.send_message(game.cid, str(e))
		
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
	


async def callback_choose_game_prop(update: Update, context: CallbackContext):
	bot = context.bot
	user_data = context.user_data
	callback = update.callback_query
	log.info('callback_choose_game_prop called: %s' % callback.data)	
	regex = re.search(r"(-[0-9]*)\*choosegamerefDE\*(.*)\*([0-9]*)", callback.data)
	cid, strcid, opcion, uid, struid = int(regex.group(1)), regex.group(1), regex.group(2), int(regex.group(3)), regex.group(3)	
	
	if cid == -1:
		await bot.edit_message_text("Cancelado", uid, callback.message.message_id)
		return	
	game = get_game(cid)
	mensaje_edit = "Has elegido el grupo {0}".format(game.groupName)	
	await bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)	
	propuesta = user_data[uid]	
	# Obtengo el juego y le agrego la pista
	await add_propose(bot, game, uid, propuesta)

async def callback_choose_game_inter(update: Update, context: CallbackContext):
	bot = context.bot
	user_data = context.user_data
	callback = update.callback_query
	log.info('callback_choose_game_prop called: %s' % callback.data)	
	regex = re.search(r"(-[0-9]*)\*choosegameintDE\*(.*)\*([0-9]*)", callback.data)
	cid, strcid, opcion, uid, struid = int(regex.group(1)), regex.group(1), regex.group(2), int(regex.group(3)), regex.group(3)	
	
	if cid == -1:
		await bot.edit_message_text("Cancelado", uid, callback.message.message_id)
		return	
	game = get_game(cid)
	mensaje_edit = "Has elegido el grupo {0}".format(game.groupName)	
	await bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)	
	propuesta = user_data[uid]	
	# Obtengo el juego y le agrego la pista
	await add_intercept(bot, game, uid, propuesta)

async def callback_choose_game_dec(update: Update, context: CallbackContext):
	bot = context.bot
	user_data = context.user_data
	callback = update.callback_query
	log.info('callback_choose_game_prop called: %s' % callback.data)	
	regex = re.search(r"(-[0-9]*)\*choosegamedecDE\*(.*)\*([0-9]*)", callback.data)
	cid, strcid, opcion, uid, struid = int(regex.group(1)), regex.group(1), regex.group(2), int(regex.group(3)), regex.group(3)	
	
	if cid == -1:
		await bot.edit_message_text("Cancelado", uid, callback.message.message_id)
		return	
	game = get_game(cid)
	mensaje_edit = "Has elegido el grupo {0}".format(game.groupName)	
	await bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)	
	propuesta = user_data[uid]	
	# Obtengo el juego y le agrego la pista
	await add_decrypt(bot, game, uid, propuesta)

async def add_intercept(bot, game, uid, propuesta):
	if game.board.state.fase_actual == "Intercept/Decrypt" and game.board.state.inactive_team.belongs(uid) and game.turncount != 1:
		
		game.board.state.active_team.opponent_team_choosen_code = "".join(x for x in propuesta if x.isdigit())
		await save(bot, game.cid)
		await DecryptController.inform_teams(bot, game)
	else:
		if not game.board.state.inactive_team.belongs(uid):
			await bot.send_message(game.cid, "No pertences al equipo que tiene que interceptar")
		else:
			await bot.send_message(game.cid, "No es el momento de interceptar")

async def add_decrypt(bot, game, uid, propuesta):
	if game.board.state.fase_actual == "Intercept/Decrypt" and game.board.state.active_team.belongs(uid):
		
		game.board.state.active_team.team_choosen_code = "".join(x for x in propuesta if x.isdigit())
		await save(bot, game.cid)
		await DecryptController.inform_teams(bot, game)
	else:
		if not game.board.state.active_team.belongs(uid):
			await bot.send_message(game.cid, "No pertences al equipo que tiene que desencriptar")
		else:
			await bot.send_message(game.cid, "No es el momento de desencriptar")

async def add_propose(bot, game, uid, propuesta):
	# Se verifica igual en caso de que quede una botonera perdida
	if uid in game.playerlist:
		#Check if there is a current game
		if game.board == None:
			await bot.send_message(game.cid, "El juego no ha comenzado!")
			return
		# If player is any of the 
		if uid == ADMIN[0] or (uid in [team.active_player.uid for team in game.board.state.teams]):
			await bot.send_message(uid, "Tu referencia: {} fue agregada.".format(propuesta))	

			game.getPlayerTeam(uid).clue = propuesta			
			await save(bot, game.cid)
			# Si ambos encriptadores pusieron su pista entonces Sigue el juego.
			if None not in [team.clue for team in game.board.state.teams]:
				game.board.state.fase_actual = 'Intercept/Decrypt'
				await save(bot, game.cid)
				await DecryptController.inform_teams(bot, game)
			else:
				# Se avisa en vivo que falta que el otro jugador ponga su pista
				for player in [team.active_player for team in game.board.state.teams if team.clue == None]:
					msg = "{} falta tu codigo te estamos esperando!\n".format(player_call(player))
					await bot.send_message(player.uid, msg, ParseMode.MARKDOWN)
					await bot.send_message(game.cid, msg, ParseMode.MARKDOWN)
		else:
			await bot.send_message(uid, "No puedes poner codigo si NO sos el jugador activo o no es la fase correcta")
	else:
		await bot.send_message(uid, "No puedes hacer code si no estas en el partido.")
		
# Por async defecto no hay restricciones
async def get_choose_game_buttons(games_tipo, uid, fase_actual, commando_origen, callback_command):	
	btns = []
	cid = None
	for game_chat_id, game in games_tipo.items():
		if uid in game.playerlist and game.board != None:
			log.info('uid: {} game {}, fase actual {}'.format(uid, game.groupName , fase_actual))
			allow_only_id = game.board.state.active_team.active_player.uid
			#if uid == allow_only_id and game.board.state.fase_actual == fase_actual:
			current_game_fase = game.board.state.fase_actual
			show_button = False
			# verifico fase actual, comando de origen, y usuario para ver si le muestro el boton
			if current_game_fase == fase_actual:
				if commando_origen == 'code':
					show_button = (uid in [team.active_player.uid for team in game.board.state.teams])
				if commando_origen == 'decrypt':
					show_button = game.board.state.active_team.belongs(uid)
				if commando_origen == 'intercept':
					show_button = game.board.state.inactive_team.belongs(uid) and game.turncount != 1		
			if show_button:			
				clue_text = commando_origen
				# Pongo en cid el id del juego actual, para el caso de que haya solo 1
				cid = game_chat_id
				# Creo el boton el cual eligirá el jugador
				txtBoton = game.groupName
				comando_callback = callback_command
				datos = str(game_chat_id) + "*" + comando_callback + "*" + clue_text + "*" + str(uid)
				btns.append([InlineKeyboardButton(txtBoton, callback_data=datos)])
	return btns, cid

async def command_code(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	user_data = context.user_data
	try:
		cid = update.message.chat_id
		uid = update.message.from_user.id
		
		if update.message.chat.type in ['group', 'supergroup']:
			await bot.delete_message(cid, update.message.message_id)
			return
		
		if len(args) > 0:
			# Obtengo todos los juegos de base de datos de los que usan code
			code = ' '.join(args)
			# Verifico que sean 3 pistas y que no sean vacias o espacios.
			if len([x for x in code.split(',') if x.strip()]) == 3:
				# Si puso la cantidad de pistas correctas sigo
				mensaje_error = ""			
				games_tipo = MainController.getGamesByTipo('Decrypt')						
				btns, cid = get_choose_game_buttons(games_tipo, uid, fase_actual = 'Set_Reference', commando_origen = 'code', callback_command = 'choosegamerefDE')
				user_data[uid] = code
				
				if len(btns) != 0:
					if len(btns) == 0:
						#Si es solo 1 juego lo hago automatico
						game = get_game(cid)
						add_propose(bot, game, uid, code)
					else:
						txtBoton = "Cancel"
						datos = "-1*choosegamerefDE*" + "prop" + "*" + str(uid)
						btns.append([InlineKeyboardButton(txtBoton, callback_data=datos)])
						btnMarkup = InlineKeyboardMarkup(btns)
						await bot.send_message(uid, "En cual de estos grupos queres mandar la referencia?", reply_markup=btnMarkup)
				else:
					mensaje_error = "No hay partidas en las que puedas hacer /code"
					await bot.send_message(uid, mensaje_error)
			else:
				mensaje_error = "Debes poner 3 pistas, recuerda que cada uno se separa por coma (,) EJ: PISTA 1, *ONOMATOPEYA4*, FRASE FRASE 2"
				await bot.send_message(uid, mensaje_error)

	except Exception as e:
		await bot.send_message(uid, str(e))
		log.error("Unknown error: " + str(e))

async def command_intercept(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	user_data = context.user_data
	try:
		cid = update.message.chat_id
		uid = update.message.from_user.id
		
		if update.message.chat.type in ['group', 'supergroup']:
			await bot.delete_message(cid, update.message.message_id)
			return
		
		if len(args) > 0:
			# Obtengo todos los juegos de base de datos de los que usan clue
			mensaje_error = ""			
			games_tipo = MainController.getGamesByTipo('Decrypt')						
			
			btns, cid = get_choose_game_buttons(games_tipo, uid, fase_actual = 'Intercept/Decrypt', 
											commando_origen = 'intercept', callback_command = 'choosegameintDE')

			user_data[uid] = ' '.join(args)
			
			if len(btns) != 0:
				if len(btns) == 0:
					#Si es solo 1 juego lo hago automatico
					game = get_game(cid)
					await add_intercept(bot, game, uid, ' '.join(args))
				else:
					txtBoton = "Cancel"
					datos = "-1*choosegameintDE*" + "prop" + "*" + str(uid)
					btns.append([InlineKeyboardButton(txtBoton, callback_data=datos)])
					btnMarkup = InlineKeyboardMarkup(btns)
					await bot.send_message(uid, "En cual de estos grupos la intercepción?", reply_markup=btnMarkup)
			else:
				mensaje_error = "No hay partidas en las que puedas hacer /intercept"
				await bot.send_message(uid, mensaje_error)
	except Exception as e:
		await bot.send_message(uid, str(e))
		log.error("Unknown error: " + str(e))

async def command_decrypt(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	user_data = context.user_data
	try:
		cid = update.message.chat_id
		uid = update.message.from_user.id
		
		if update.message.chat.type in ['group', 'supergroup']:
			await bot.delete_message(cid, update.message.message_id)
			return
		
		if len(args) > 0:
			# Obtengo todos los juegos de base de datos de los que usan clue
			mensaje_error = ""			
			games_tipo = MainController.getGamesByTipo('Decrypt')						
			
			btns, cid = get_choose_game_buttons(games_tipo, uid, fase_actual = 'Intercept/Decrypt', 
												commando_origen = 'decrypt', callback_command = 'choosegamedecDE')

			user_data[uid] = ' '.join(args)
			
			if len(btns) != 0:
				if len(btns) == 0:
					#Si es solo 1 juego lo hago automatico
					game = get_game(cid)
					await add_decrypt(bot, game, uid, ' '.join(args))
				else:
					txtBoton = "Cancel"
					datos = "-1*choosegamedecDE*" + "prop" + "*" + str(uid)
					btns.append([InlineKeyboardButton(txtBoton, callback_data=datos)])
					btnMarkup = InlineKeyboardMarkup(btns)
					await bot.send_message(uid, "En cual de estos grupo realizas la desencripción?", reply_markup=btnMarkup)
			else:
				mensaje_error = "No hay partidas en las que puedas hacer /decrypt"
				await bot.send_message(uid, mensaje_error)
	except Exception as e:
		await bot.send_message(uid, str(e))
		log.error("Unknown error: " + str(e))
		raise e
		
