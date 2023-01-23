#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Eduardo Peluffo"

import copy
import json
import logging as log
import re
from random import randrange, shuffle
from time import sleep

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update, ForceReply, Update
from telegram.ext import (Updater, CommandHandler, CallbackQueryHandler, CallbackContext)

from Utils import get_game, save
from Constants.Config import ADMIN

from Arcana.Constants.Config import DIFFICULTAD
from Arcana.Constants.Cards import FATETOKENS, LASHORAS, ARCANACARDS, PLAYERFATETOKENS

from Arcana.Boardgamebox.Game import Game
from Arcana.Boardgamebox.Player import Player
from Arcana.Boardgamebox.Board import Board

from Utils import (increment_player_counter, player_call, simple_choose_buttons, get_game)

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
		call_diff_buttons(bot, game)
	except Exception as e:
		bot.send_message(game.cid, 'No se ejecuto el comando debido a: '+str(e))

def call_diff_buttons(bot, game):
	#log.info('call_dicc_buttons called')
	opciones_botones = DIFFICULTAD
	simple_choose_buttons(bot, game.cid, 1234, game.cid, "choosediccAR", "Elija difficultad para jugar", opciones_botones)
	
def callback_finish_config(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_finish_config_sayanything called')
	callback = update.callback_query
	try:
		regex = re.search(r"(-[0-9]*)\*choosediccAR\*(.*)\*([0-9]*)", callback.data)
		cid, opcion, uid = int(regex.group(1)), regex.group(2), int(regex.group(3)), 
		mensaje_edit = "Por la difficultad el doom comienza en: {0}".format(opcion)
		
		#update.callback_query.answer(text="Si ningún destino visible es exactamente 1 más o 1 menos que cualquiera de tus destinos, jugá uno de ellos aquí.", show_alert=False)
		
		try:
			bot.edit_message_text(mensaje_edit, cid, callback.message.message_id)
		except Exception as e:
			bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)			
		game = get_game(cid)
		game.configs['difficultad'] = opcion
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
	# Seteo la difficultad
	# Si es modo Hardcore...
	if opcion == "-1":
		opcion = "6"
		game.configs['difficultadNombre'] = "Hardcore"
	game.board.state.doom = int(opcion)
	# Antes de comenzar la ronda saco 4 cartas de arca, en proximas rondas la cantidad se ajustara en la fase de Fade	
	game.board.state.arcanasOnTable.append(LASHORAS)
	for i in range(4):
		game.board.state.arcanasOnTable.append(game.board.arcanaCards.pop())
	
	start_round(bot, game)

# Objetivo
# start_round / Draw Fates -> Play Fate -> Predict or Pass ->   Resolve  -> Fade
#  ---------------"Jugar Fate"---------     --Predecir ---     ----Resolver------
	
def start_round(bot, game):
	log.info('start_round_Arcana called')
	cid = game.cid	
	# Se marca al jugador activo
	
	# Se resetean marcas del turno
	game.board.state.plusOneEnable = False
	game.board.state.used_sacar = False
	game.board.state.extraGuess = 0
	game.board.state.used_fate_power = False
	
	active_player = game.player_sequence[game.board.state.player_counter]	
	game.board.state.active_player = active_player
	
	draw_fates_player(bot, game, game.board.state.active_player)
	game.board.state.fase_actual = "Jugar Fate"
	save(bot, game.cid)
	
	show_fates_active_player(bot, game)	
	#send_buttons_active_player(bot, game)
	#bot.send_message(cid, game.board.print_board(game), ParseMode.MARKDOWN)
	game.board.print_board(bot, game)
	msg = "{} tienes que poner un destino sobre alguna Arcana!".format(player_call(game.board.state.active_player))
	bot.send_message(game.cid, msg, ParseMode.MARKDOWN)
	#print_board(bot, game)
	
	show_player_fate_tokens_active_player(bot, game)

def show_board(bot, game):
	game.board.print_board(bot, game)
	show_fates_active_player(bot, game)
	
def draw_fates_player(bot, game, player):
	# El jugador obtiene hasta 2 
	draw_tokens = 2-len(player.fateTokens)	
	for i in range(draw_tokens):
		player.fateTokens.append(game.board.draw_fate_token())
	player.amount_tokens_draw = draw_tokens
	msg = "El jugador *{}* ha robado *{}* tokens de destino".format(player.name, draw_tokens)
	bot.send_message(game.cid, msg, parse_mode=ParseMode.MARKDOWN)	
	game.history.append(msg)
def show_fates_active_player(bot, game):
	log.info('show_fates_active_player called')
	cid = game.cid
	active_player = game.board.state.active_player
	mensaje = "Partida: {}\n*Has robado {} tokens.\nLos tokens que tiene en tu mano son (Has click sobre uno de ellos para agregarlo a una Arcana):*".format(game.groupName, active_player.amount_tokens_draw)
	btns = []
	index = 0
	for fate in active_player.fateTokens:
		if (active_player.amount_tokens_draw == 2 or (active_player.amount_tokens_draw == 1 and index == 1)):
			texto = fate["Texto"]
			horas = fate["TimeSymbols"]
			texto_alternativo = "{} {}".format("{} ({})".format(texto, horas), "(Nuevo)")
		else:
			texto_alternativo = None
		
		btns.append([create_fate_button(fate, cid, active_player.uid, index, "chooseFateAR", texto_alternativo)])
		index += 1
	btnMarkup = InlineKeyboardMarkup(btns)
	bot.send_message(active_player.uid, mensaje, parse_mode=ParseMode.MARKDOWN, reply_markup=btnMarkup)

def show_player_fate_tokens_active_player(bot, game, message_id = None):
	log.info('show_player_fate_tokens_active_player called')
	cid = game.cid
	active_player = game.board.state.active_player
	mensaje = "*Tokens Frente a Jugador*"
	btns = []
	index = 0
	for fate in active_player.playerFateTokens:
		btns.append(create_fate_button(fate, cid, active_player.uid, index, "ToggleFateAC"))
		index += 1
	btnMarkup = InlineKeyboardMarkup([btns])	
	if message_id:
		bot.edit_message_text(mensaje, chat_id=cid, message_id=message_id, 
				      parse_mode=ParseMode.MARKDOWN, reply_markup=btnMarkup)
	else:
		bot.send_message(cid, mensaje, parse_mode=ParseMode.MARKDOWN, reply_markup=btnMarkup, timeout=30)

def callback_toggle_fate_action(bot, cid, opcion, index, uid, message_id):
	game = get_game(cid)
	active_player = game.board.state.active_player
	# El active player no puede usar el comando.
	if active_player.uid != uid:
		choose_fate = active_player.playerFateTokens[index-1]
		choose_fate["Enable"] = False if choose_fate["Enable"] else True
		show_player_fate_tokens_active_player(bot, game, message_id)
		
def callback_choose_fate(update: Update, context: CallbackContext):
	bot = context.bot
	user_data = context.user_data
	callback = update.callback_query
	try:		
		#log.info('callback_finish_game_buttons called: %s' % callback.data)	
		regex = re.search(r"(-[0-9]*)\*chooseFateAR\*(.*)\*(-?[0-9]*)", callback.data)
		cid, index = int(regex.group(1)), int(regex.group(3))		
		
		uid = update.effective_user.id
		
		game = get_game(cid)
		
		if game.board.state.fase_actual != "Jugar Fate" or uid != game.board.state.active_player.uid:
			bot.send_message(cid, "No es el momento de jugar destino o no eres el que tiene que jugar el fate", ParseMode.MARKDOWN)
				
		active_player = game.board.state.active_player
		fate = active_player.fateTokens[index]
		user_data['fate'] = fate
		user_data['unchosen'] = active_player.fateTokens[1 if index == 0 else 0]
		
		texto = fate["Texto"]
		horas = fate["TimeSymbols"]			
		
		#update.callback_query.answer(text="{} ({})".format(texto, horas), show_alert=False)
		
		bot.edit_message_text("Partida: {}\nHas elegido el destino *{}*".format(game.groupName, texto), uid, callback.message.message_id, parse_mode=ParseMode.MARKDOWN)
		
		#"Elige en que Arcana quieres ponerlo."
		btns = []
		i = 0
		for arcana_on_table in game.board.state.arcanasOnTable:
			btns.append([game.board.create_arcana_button(game.cid, arcana_on_table, i, comando_callback = "chooseArcanaAR")])
			i += 1
		# Agrego boton cancelar
		datos = str(cid) + "*chooseArcanaAR*Cancelar*" + str(-1)
		btns.append([InlineKeyboardButton("Cancelar", callback_data=datos)])
		btnMarkup = InlineKeyboardMarkup(btns)
		bot.send_message(uid, "Partida {}\n*Elige en que Arcana quieres ponerlo.*:".format(game.groupName), parse_mode=ParseMode.MARKDOWN, reply_markup=btnMarkup)
		
	except Exception as e:
		bot.send_message(ADMIN[0], 'No se ejecuto el comando de callback_choose_fate debido a: '+str(e))
		bot.send_message(ADMIN[0], callback.data)

def callback_choose_arcana(update: Update, context: CallbackContext):
	bot = context.bot
	user_data = context.user_data
	callback = update.callback_query
			
	#log.info('callback_finish_game_buttons called: %s' % callback.data)	
	regex = re.search("(-[0-9]*)\*chooseArcanaAR\*(.*)\*(-?[0-9]*)", callback.data)
	cid, strcid, opcion, index = int(regex.group(1)), regex.group(1), regex.group(2), int(regex.group(3))
	#bot.send_message(ADMIN[0], struid)

	uid = update.effective_user.id
	game = get_game(cid)
	try:	
		if game.board.state.fase_actual != "Jugar Fate" or uid != game.board.state.active_player.uid:
			bot.send_message(cid, "No es el momento de jugar destino o no eres el que tiene que jugar el fate", ParseMode.MARKDOWN)

		if index == -1:
			bot.edit_message_text("Accion cancelada se vuelven a enviar destinos\n", uid, callback.message.message_id)
			show_fates_active_player(bot, game)
			return

		arcana = game.board.state.arcanasOnTable[index]
		texto = arcana["Texto"]
		titulo = arcana["Título"]
		chosen_fate = user_data['fate']
		unchosen_fate = user_data['unchosen']

		# Caso particular de elegir +1
		if game.board.state.plusOneEnable:
			unchosen_fate = copy.deepcopy(user_data['unchosen'])
			unchosen_fate["Texto"] = "{}".format(int(unchosen_fate["Texto"])+1)
			
		is_legal_arcana = game.board.is_legal_arcana(arcana, chosen_fate, unchosen_fate)
		
		# Verifico que no haya posibles arcanas si se elija a "Las Horas"
		if titulo == "Las horas":
			log.info('get_valid_arcanas called')
			valid_arcanas_fates = game.board.get_valid_arcanas(chosen_fate, unchosen_fate)
			log.info('get_valid_arcanas finished')
			if len(valid_arcanas_fates) > 0:
				msg = "Puedes usar estas arcanas y combinaciones (Choose fate / unchoose fate)\n"
				for valid_arcana_fates in valid_arcanas_fates:
					msg += "Arcana: *{}*, Poner fate: *{}*.\n".format(
						valid_arcana_fates[0]["Título"], valid_arcana_fates[1]["Texto"])									
				bot.send_message(uid, msg, ParseMode.MARKDOWN)
				is_legal_arcana = False
				
		if not is_legal_arcana:
			bot.edit_message_text("No puedes jugar ese destino en esa arcana, se vuelven a enviar destinos\n", uid, callback.message.message_id)
			show_fates_active_player(bot, game)
			return

		if 'tokens' not in arcana:
			arcana['tokens'] = []		

		update.callback_query.answer(text="Se puso en la arcana {} el destino {}".format(arcana["Título"], chosen_fate["Texto"]), show_alert=False)

		bot.edit_message_text("Partida: {}\nHas elegido la Arcana *{}: {}*.\nTe queda en la mano el token *{}*\n".format(game.groupName, titulo, texto, user_data['unchosen']["Texto"]), uid, callback.message.message_id, parse_mode=ParseMode.MARKDOWN)

		mensaje_final = "El jugador *{}* ha puesto el destino *{}* en la Arcana *{}*.".format(
			game.board.state.active_player.name, chosen_fate["Texto"], arcana["Título"])
		
		game.board.state.active_player.last_chosen_fate = chosen_fate
		
		# Caminos alternativo si elige una arcana especial. Y si detiende la ejecucion del metodo.
		if(aditional_actions_arcanas(bot, game, index, arcana, titulo, texto, uid, callback, mensaje_final, chosen_fate)):
			return

		if titulo == "Las horas":
			arcana = game.board.state.arcanasOnTable[index+1]
			texto = arcana["Texto"]
			mensaje_final += "\nComo se ha jugado en Las Horas el token pasa a la siguiente arcana *{}*".format(arcana["Título"])			

		call_other_players = ""
		for uid, player in game.playerlist.items():
			call_other_players += "{} ".format(player_call(player)) if uid != game.board.state.active_player.uid else ""
		
		game.history.append(mensaje_final)
		mensaje_final += "\n{}Hagan /guess N para adivinar destino o /pass para pasar!".format(call_other_players)	
		arcana['tokens'].append(chosen_fate)		
		game.board.state.active_player.fateTokens.remove(chosen_fate)
		game.board.state.fase_actual = "Predecir"
		save(bot, game.cid)
		game.board.print_board(bot, game)		
		bot.send_message(cid, mensaje_final, ParseMode.MARKDOWN, timeout=30)
		show_player_fate_tokens_active_player(bot, game)
	except Exception as e:
		bot.send_message(ADMIN[0], 'No se ejecuto el comando de callback_choose_arcana debido a: '+str(e))
		bot.send_message(ADMIN[0], callback.data)

# Acciones particulares de la Arcana Sacar.
def aditional_actions_arcanas(bot, game, index, arcana, titulo, texto, uid, callback, mensaje, chosen_fate):
	stop_flow = False
	if arcana["Título"] == "Sacar":	
		arcana['tokens'].append(chosen_fate)		
		game.board.state.active_player.fateTokens.remove(chosen_fate)
		game.history.append(mensaje)
		bot.send_message(game.cid, mensaje, ParseMode.MARKDOWN)
		game.board.state.used_sacar = True
		draw_fates_player(bot, game, game.board.state.active_player)
		show_fates_active_player(bot, game)
		save(bot, game.cid)
		stop_flow = True
	if arcana["Título"] == "Adivinar":
		game.board.state.extraGuess += 1		
	return stop_flow
	
def create_fate_button(fate, cid, uid, index, comando_callback = "chooseFateAR", alternative_text = None):
	texto = fate["Texto"]
	horas = fate["TimeSymbols"]
	# Los tokens de recordatorio de usuario tienen enable en ellos.
	if "Enable" not in fate:
		txtBoton = "{} ({})".format(texto, horas)
	elif "Enable" in fate and fate["Enable"]:
		txtBoton = "{}".format(texto)
	else:
		txtBoton = "X"		
	comando_callback = comando_callback
	uid = cid # Solo se va a usar para mostrar en pantallas de juego
	datos = str(cid) + "*" + comando_callback + "*" + str(texto) + "*" + str(index)
	if alternative_text:
		return InlineKeyboardButton(alternative_text, callback_data=datos)
	else:
		return InlineKeyboardButton(txtBoton, callback_data=datos)	
	
def resolve(bot, game, prediccion = []):	
	# Si los jugadores hicieron una prediccion (se pasa el argumento como string)
	good_prediction = False
	
	if len(prediccion) > 0:
		fate_quedaba = game.board.state.active_player.fateTokens.pop()		
		if int(fate_quedaba["Texto"]) in prediccion:
			# Si predicen bien el faden no aumenta el doom.
			game.board.state.score += 1
			good_prediction = True
			bot.send_message(game.cid, "*Correcto!* El destino que tenia el jugador era {}, se gana 1 punto!"
					 .format(fate_quedaba["Texto"]), ParseMode.MARKDOWN)
		else:			
			game.board.state.doom  += 1
			bot.send_message(game.cid, "*Incorrecto!* El destino que tenia el jugador era {}"
					 .format(fate_quedaba["Texto"]), ParseMode.MARKDOWN)	
		game.board.fateTokens.append(fate_quedaba)
		for fate in game.board.state.active_player.playerFateTokens:
			fate["Enable"] = True
	
	# Fading phase
	arcanasOnTable = game.board.state.arcanasOnTable	
	for arcana_on_table in arcanasOnTable:
		#print(arcana_on_table)
		if 'tokens' not in arcana_on_table:
			arcana_on_table['tokens'] = []
		if game.board.count_fate_tokens(arcana_on_table) >= int(arcana_on_table["Lunas"]):
			fadding_arcana(arcanasOnTable, arcana_on_table, game, good_prediction)
			msg = "La Arcana *{}* se ha desvanecido".format(arcana_on_table["Título"])
			game.history.append(msg)
			bot.send_message(game.cid, msg, ParseMode.MARKDOWN)
	start_next_round(bot, game)			
	
def fadding_arcana(arcanasOnTable, arcana_on_table, game, good_prediction):
	indice = arcanasOnTable.index(arcana_on_table)
	# Regreso los tokens de destino a la bolsa
	game.board.fateTokens.extend(arcana_on_table['tokens'])
	# La doy vuelta y la pongo en la "faded area"
	arcana_on_table["faded"] = True
	arcana_on_table['tokens'] = []
	game.board.state.fadedarcanasOnTable.append(arcana_on_table)
	# Si no hubo buena prediccion avanzo doom 2, a menos que la arcana sea Libre.
	if not good_prediction and arcana_on_table["Título"] != "Libre":
		game.board.state.doom  += 2
	# Reemplazo arcana
	arcanasOnTable[indice] = game.board.arcanaCards.pop()
	if len(game.board.arcanaCards) == 1:
		shuffle(game.board.state.discardedArcanas)
		game.board.arcanaCards.extend(game.board.state.discardedArcanas)
		game.board.state.discardedArcanas = []
		
def start_next_round(bot, game):
	log.info('Verifing End_Game called')
	try:
		diffMode = game.configs.get('difficultadNombre', "Normal")
	except Exception:
		diffMode = "Normal"
	if (game.board.state.score > 6 and diffMode != "Hardcore") or game.board.state.doom > 6:
		# Si no quedan cartas se termina el juego y se muestra el puntaje.
		mensaje = "Juego finalizado!:\n*{0}*".format(game.board.print_result(game))
		game.board.state.fase_actual = "Finalizado"
		save(bot, game.cid)
		bot.send_message(game.cid, mensaje, ParseMode.MARKDOWN)
		continue_playing(bot, game)
		return
	increment_player_counter(game)
	start_round(bot, game)

def continue_playing(bot, game):
	opciones_botones = { "Nuevo" : "Cambiar jugadores", "Misma Dificultad" : "Misma Dificultad", "Cambiar Dificultad" : "Cambiar Dificultad"}
	simple_choose_buttons(bot, game.cid, 1, game.cid, "chooseendAR", "¿Quieres continuar jugando?", opciones_botones)
	
def callback_finish_game_buttons(update: Update, context: CallbackContext):
	bot = context.bot
	callback = update.callback_query
	try:		
		#log.info('callback_finish_game_buttons called: %s' % callback.data)	
		regex = re.search("(-[0-9]*)\*chooseendAR\*(.*)\*([0-9]*)", callback.data)
		cid, strcid, opcion, uid, struid = int(regex.group(1)), regex.group(1), regex.group(2), int(regex.group(3)), regex.group(3)
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
		try:
			diffMode = game.configs.get('difficultadNombre', "Normal")
		except Exception as e:
			diffMode = "Normal"
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
		#log.info('Llego hasta la creacion')		
		for uid in players:		
			game.add_player(uid, players[uid].name)		
		# StartGame
		player_number = len(game.playerlist)
		game.board = Board(player_number, game)		
		game.player_sequence = []
		game.shuffle_player_sequence()
					
		if opcion == "Misma Dificultad":
			game.configs['difficultad'] = diff
			game.configs['difficultadNombre'] = diffMode
			finish_config(bot, game, diff)
		if opcion == "Cambiar Dificultad":
			#(Beta) Nuevo Partido, mismos jugadores, diferente diccionario
			call_diff_buttons(bot, game)				
	except Exception as e:
		bot.send_message(ADMIN[0], 'No se ejecuto el comando debido a: '+str(e))
		bot.send_message(ADMIN[0], callback.data)
	
def callback_txt_arcana(update: Update, context: CallbackContext):
	bot = context.bot
	callback = update.callback_query
	try:		
		#log.info('callback_txt_arcana called: %s' % callback.data)
		regex = re.search(r"(-[0-9]*)\*txtArcanaAR\*(.*)\*(-?[0-9]*)", callback.data)
		opcion, index = regex.group(2), int(regex.group(3))
		#bot.send_message(ADMIN[0], struid)
		faded = False
		if opcion == "Las horas":
			arcana = LASHORAS
		else:
			arcana = next((item for item in ARCANACARDS if item["Título"] == opcion), -1)
			if arcana == -1 or index == -2:
				arcana = next(item for item in ARCANACARDS if item["Título reverso"] == opcion)
				faded = True
		#log.info((arcana, faded))
		if faded:
			texto = arcana["Texto reverso"]
			titulo = arcana["Título reverso"]
		else:
			texto = arcana["Texto"]
			titulo = arcana["Título"]
		update.callback_query.answer(text="{}: {}".format(titulo, texto), show_alert=True)
	except Exception as e:
		bot.send_message(ADMIN[0], 'No se ejecuto el comando de callback_txt_arcana debido a: '+str(e))
		bot.send_message(ADMIN[0], callback.data)

# Si se usa la accion se descarta al final.
def use_fadded_action(bot, game, uid, elegido):
	arcana = game.board.state.fadedarcanasOnTable[elegido]
	# Verifico que puede usarla y aparte no se haya usado una ya.
	if can_use_fadded(bot, game, uid, arcana) and not game.board.state.used_fate_power:
		
		# 3 acciones que cambian cartas en arcanas Reubicar Ciclar Descartar menor
		titulo = arcana["Título reverso"]
		accion = {"+1" : plusOneAction, 
			  "Reubicar": reubicar_action, 
			  "Ciclar": ciclar_action, 
			  "Descartar menor": descartarmenor_action,
			  "Repetir" : repetir_action,
			  "1-2-3" : action_123,
			  "1-4-7" : action_147,
			  "3-4-5" : action_345,
			  "5-6-7" : action_567,
			  "¿Dentro de 2?" : dentroDe2_action,
			 }.get(titulo)
		if accion:
			done = accion(bot, game, uid)
			if done == 1:
				game.board.state.fadedarcanasOnTable.remove(arcana)
				arcana["faded"] = False
				arcana['tokens'] = []
				game.board.state.discardedArcanas.append(arcana)
				#game.board.arcanaCards.append(arcana)				
				game.board.state.used_fate_power = True
				bot.send_message(game.cid, "Se ha removido la arcana *{}* con habilidad *{}*".format(arcana["Título reverso"], arcana["Texto reverso"]), ParseMode.MARKDOWN)						
			elif done == 0:
				bot.send_message(game.cid, "Se esta ejecutandola arcana *{}*".format(arcana["Título reverso"]), ParseMode.MARKDOWN)						
			else:
				bot.send_message(game.cid, "No puedes usar esta arcana ahora o Funcionalidad de *{}* en *Construcción*".format(arcana["Título reverso"]), ParseMode.MARKDOWN)
		else:
			# Por el momento el resto se ejecutaran directamente.
			game.board.state.used_fate_power = True
			game.board.state.fadedarcanasOnTable.remove(arcana)
			arcana["faded"] = False
			arcana['tokens'] = []
			#game.board.arcanaCards.append(arcana)
			game.board.state.discardedArcanas.append(arcana)
			bot.send_message(game.cid, "Se ha removido la arcana *{}* con habilidad *{}*".format(arcana["Título reverso"], arcana["Texto reverso"]), ParseMode.MARKDOWN)		
		save(bot, game.cid)
	else:
		bot.send_message(game.cid, "No se puede/No puedes usar este poder en este momento", ParseMode.MARKDOWN)

def plusOneAction(bot, game, uid):
	game.board.state.plusOneEnable = True
	game.history.append("Se ha usado +1 en la arcana no utilizada.")
	return 1
def ciclar_action(bot, game, uid):
	log.info('ciclar_action called')
	arcanas_con_fate = [arcana["Título"] for arcana in game.board.state.arcanasOnTable if len(arcana['tokens']) > 0 ]
	arcanas_con_fate.append("Las horas")
	if len(arcanas_con_fate) == 5:
		# Si todas tienen arcanas no se puede usar
		return False
				
	btnMarkup = create_arcanas_buttons(bot, game, "Ciclar", uid, restrict = arcanas_con_fate)
	bot.send_message(uid, "Partida {}\n*Elige Arcana a descartar:*".format(game.groupName), parse_mode=ParseMode.MARKDOWN, reply_markup=btnMarkup)
	
	return 0

# Mostrar destinos Arcana (Cancel muestra arcanas)
# Verificar que el destino a eliminar sea menor al destino restante
def descartarmenor_action(bot, game, uid):
	log.info('descartarmenor_action called')
	fate_quedaba = int(game.board.state.active_player.fateTokens[0]["Texto"])
	# Se filtran arcanas que no tengan tokens o cuyos tokens sean todos mayores o iguales al restante.
	restringir_arcanas = [arcana["Título"] for arcana in game.board.state.arcanasOnTable 
			      if (len(arcana['tokens']) == 0 or all(fate_quedaba <= int(token["Texto"]) for token in arcana['tokens']))]	
	btnMarkup = create_arcanas_buttons(bot, game, "DescartarMenor", uid, restrict = restringir_arcanas)
	bot.send_message(uid, "Partida {}\n*Elige Arcana para sacar destino.*:".format(game.groupName), parse_mode=ParseMode.MARKDOWN, reply_markup=btnMarkup)
	return 0

def reubicar_action(bot, game, uid):
	log.info('reubicar_action called')
	restringir_arcanas = [arcana["Título"] for arcana in game.board.state.arcanasOnTable if len(arcana['tokens']) == 0]
	btnMarkup = create_arcanas_buttons(bot, game, "ReubicarOrigen", uid, restrict = restringir_arcanas)
	bot.send_message(uid, "Partida {}\n*Elige Arcana a la que quieres queitar un token*:".format(game.groupName), parse_mode=ParseMode.MARKDOWN, reply_markup=btnMarkup)
	return 0
	# Botones Publicos
	# El jugador mueve destino de una arcana a otra.
	# Mostrar arcanas (menos las horas) (Cancel jugador no decide más)
	# Mostrar destinos Arcana (Cancel muestra arcanas)
	# Mostrar arcanas posibles (Cancel muestra destinos de nuevo)
	# Verificar que la arcana no sea la misma

def callback_reubicar_origen_action(bot, cid, opcion, index, uid, message_id):
	game = get_game(cid)
	if index != -1:
		arcana = game.board.state.arcanasOnTable[index]
		btnMarkup = create_fate_buttons(bot, game, 'ReubicarOrigen', uid, arcana, index, 0, 8)		
		bot.edit_message_text("Partida {}\n*Elige Token a reubicar.*:".format(game.groupName), 
				      chat_id=uid, message_id=message_id, 
				      parse_mode=ParseMode.MARKDOWN, reply_markup=btnMarkup)
	else:
		bot.edit_message_text("*Accion cancelada*", chat_id=uid, message_id=message_id, parse_mode=ParseMode.MARKDOWN)

def callback_reubicar_destino_action(bot, cid, opcion, index, uid, message_id):
	game = get_game(cid)	
	# Chequeo que la arcana desvanecida sigue vigente
	faded_arcana = next((x for x in game.board.state.fadedarcanasOnTable if x["Título reverso"] == 'Reubicar'), None)
	if faded_arcana != None and index != -1:
		# Arcana de destino
		arcanaDestino = game.board.state.arcanasOnTable[index]
		# Obtengo arcana de origen y su index 
		arcana_index_origen = game.board.state.indexArcanaOrigen
		fate_index_origen = game.board.state.indexFateArcanaOrigen		
		
		arcanaOrigen = game.board.state.arcanasOnTable[arcana_index_origen]		
		# Saco el token del origen
		fate_movido = arcanaOrigen['tokens'].pop(fate_index_origen)
		arcanaDestino['tokens'].append(fate_movido)		
		msg = "*Se ha pasado el token {} de la arcana {} a la arcana {}*:".format(fate_movido["Texto"],
											  arcanaOrigen['Título'],
											  arcanaDestino['Título'])
		bot.edit_message_text(msg, chat_id=uid, message_id=message_id, parse_mode=ParseMode.MARKDOWN)
		bot.send_message(cid, msg, parse_mode=ParseMode.MARKDOWN)
		game.history.append(msg)
		
		# Reseteo los valores de origen
		game.board.state.indexArcanaOrigen = -99
		game.board.state.indexFateArcanaOrigen = -99
		faded_arcana["faded"] = False
		faded_arcana['tokens'] = []
		game.board.state.fadedarcanasOnTable.remove(faded_arcana)
		game.board.state.discardedArcanas.append(faded_arcana)
		game.board.print_board(bot, game)
		
	else:
		bot.edit_message_text("*Accion cancelada*", chat_id=uid, message_id=message_id, parse_mode=ParseMode.MARKDOWN)

# El jugador eligio arcana para sacar tokens de destino
def callback_ciclar_action(bot, cid, opcion, index, uid, message_id):
	game = get_game(cid)
	faded_arcana = next((x for x in game.board.state.fadedarcanasOnTable if x["Título reverso"] == 'Ciclar'), None)
	
	if faded_arcana != None and index != -1:		
		game.board.state.arcanasOnTable[index] = game.board.arcanaCards.pop()
		game.board.state.fadedarcanasOnTable.remove(faded_arcana)
		faded_arcana["faded"] = False
		faded_arcana['tokens'] = []
		#game.board.arcanaCards.append(faded_arcana)
		game.board.state.discardedArcanas.append(faded_arcana)

		if len(game.board.arcanaCards) == 1:
			game.board.arcanaCards.extend(game.board.state.discardedArcanas)
			game.board.state.discardedArcanas = []

		game.board.state.used_fate_power = True
		msg = "Se ha cambiado la arcana {} por {}".format(opcion, game.board.state.arcanasOnTable[index]['Título'])
		game.history.append(msg)
		bot.edit_message_text(msg, chat_id=uid, message_id=message_id, parse_mode=ParseMode.MARKDOWN)
		game.board.print_board(bot, game)
	else:
		bot.edit_message_text("*Accion cancelada*", chat_id=uid, message_id=message_id, parse_mode=ParseMode.MARKDOWN)

def callback_descartarmenor_elegir_destino(bot, cid, opcion, index, uid, message_id):
	game = get_game(cid)
	faded_arcana = next((x for x in game.board.state.fadedarcanasOnTable if x["Título reverso"] == 'Descartar menor'), None)
	# Chequeo que la arcana desvanecida sigue vigente
	if faded_arcana != None and index != -1:		
		fate_quedaba = int(game.board.state.active_player.fateTokens[0]["Texto"])
		arcana = game.board.state.arcanasOnTable[index]
		btnMarkup = create_fate_buttons(bot, game, 'DescartarMenor', uid, arcana, index, 0, fate_quedaba)		
		bot.edit_message_text("Partida {}\n*Elige Token a descartar.*:".format(game.groupName), 
				      chat_id=uid, message_id=message_id, 
				      parse_mode=ParseMode.MARKDOWN, reply_markup=btnMarkup)
	else:
		bot.edit_message_text("*Accion cancelada*", chat_id=uid, message_id=message_id, parse_mode=ParseMode.MARKDOWN)

def callback_descartarmenor_descartar_destino(bot, cid, arcana_index, fate_index, uid, message_id):
	game = get_game(cid)
	faded_arcana = next((x for x in game.board.state.fadedarcanasOnTable if x["Título reverso"] == 'Descartar menor'), None)
	# Verifico que la fadded este todavia
	if faded_arcana != None and fate_index != -1:
		arcana = game.board.state.arcanasOnTable[arcana_index]
		fate_descartado = arcana['tokens'].pop(fate_index)
		game.board.fateTokens.append(fate_descartado)		
		msg = "Se ha eliminado el token *{}* de la arcana *{}*".format(fate_descartado["Texto"], arcana['Título'])
		game.board.state.fadedarcanasOnTable.remove(faded_arcana)
		faded_arcana["faded"] = False
		faded_arcana['tokens'] = []
		#game.board.arcanaCards.append(faded_arcana)
		game.board.state.discardedArcanas.append(faded_arcana)
		game.board.state.used_fate_power = True
		bot.edit_message_text(msg, chat_id=uid, message_id=message_id, parse_mode=ParseMode.MARKDOWN)
		game.history.append(msg)
		game.board.print_board(bot, game)
		bot.send_message(cid, msg, parse_mode=ParseMode.MARKDOWN)		
	else:
		bot.edit_message_text("*Accion cancelada*", chat_id=uid, message_id=message_id, parse_mode=ParseMode.MARKDOWN)	

# Cuando una arcana es elegida en un boton de accion termina aca.
def callback_choose_arcana_action(update: Update, context: CallbackContext):
	bot = context.bot
	callback = update.callback_query
		
	log.info('callback_choose_arcana_action called: %s' % callback.data)
	regex = re.search(r"(-?[0-9]*)\*([A-Za-z]*)ArcanaAC\*(.*)\*(-?[0-9]*)", callback.data)
	cid, accion, opcion, index = int(regex.group(1)), regex.group(2), regex.group(3), int(regex.group(4))
	uid = update.effective_user.id
	
	callback_accion = {"ReubicarDestino": callback_reubicar_destino_action,
			   "Ciclar": callback_ciclar_action,
			   "DescartarMenor": callback_descartarmenor_elegir_destino,
			   "ReubicarOrigen" : callback_reubicar_origen_action
			  }.get(accion)

	if callback_accion:
		callback_accion(bot, cid, opcion, index, uid, callback.message.message_id)
	else:
		update.callback_query.answer(text="No esta definida la funcion", show_alert=True)		

# Recibo la index de la arcana y el fate.
def callback_reubicar_fate(bot, cid, arcana_index, fate_index, uid, message_id):
	# Recibo el id de la arcana y el token a reubicar y los guardo en el state.
	game = get_game(cid)
	# Chequeo que la arcana desvanecida sigue vigente
	faded_arcana = next((x for x in game.board.state.fadedarcanasOnTable if x["Título reverso"] == 'Reubicar'), None)
	if faded_arcana != None and fate_index != -1:
		# Si todo esta bien seteo el id de arcana de origen y id de token de origen
		game.board.state.indexArcanaOrigen = arcana_index
		game.board.state.indexFateArcanaOrigen = fate_index
		# Se restrige la arcana de origen
		restringir_arcanas = [arcana_index]
		btnMarkup = create_arcanas_buttons(bot, game, "ReubicarDestino", uid, restrict = restringir_arcanas)
		bot.send_message(game.board.state.active_player.uid, "Seleccione la arcana de destino", parse_mode=ParseMode.MARKDOWN, reply_markup=btnMarkup)		
	else:
		bot.edit_message_text("*Accion cancelada*", chat_id=uid, message_id=message_id, parse_mode=ParseMode.MARKDOWN)
	
	#bot.send_message(ADMIN[0], "No esta definida la funcion".format(cid, accion, opcion, index))
		
# Cuando un destino es elegido en una accion termina aca.
def callback_choose_fate_action(update: Update, context: CallbackContext):
	bot = context.bot
	callback = update.callback_query
	try:		
		log.info('callback_choose_fate_action called: %s' % callback.data)
		regex = re.search(r"(-?[0-9]*)\*([A-Za-z]*)FateAC\*(.*)\*(-?[0-9]*)", callback.data)
		cid, accion, fate_index, arcana_index = int(regex.group(1)), regex.group(2), int(regex.group(3)), int(regex.group(4))
		uid = update.effective_user.id
		'''
		update.callback_query.answer(text="cid: {}, accion: {}, opcion: {}, index: {}"
					     .format(cid, accion, opcion, index), show_alert=True)
		'''
		callback_accion = {"ReubicarOrigen": callback_reubicar_fate,
				   "Ciclar": callback_ciclar_action,
				   "DescartarMenor": callback_descartarmenor_descartar_destino,
				   "Toggle": callback_toggle_fate_action
				  }.get(accion)
		
		if callback_accion:
			callback_accion(bot, cid, arcana_index, fate_index, uid, callback.message.message_id)
		else:
			update.callback_query.answer(text="No esta definida la funcion. Data cid {}, accion {}, opcion {}, fate_index {}, arcana_index {}"
					     .format(cid, accion, accion, fate_index, arcana_index), show_alert=True)		
	except Exception as e:
		bot.send_message(ADMIN[0], 'No se ejecuto el comando de callback_choose_fate_action debido a: '+str(e))
		bot.send_message(ADMIN[0], callback.data)
		bot.send_message(ADMIN[0], "No esta definida la funcion. Data cid {}, accion {}, opcion {}, fate_index {}, arcana_index {}".format(cid, accion, accion, fate_index, arcana_index))

# Accion a realizar, usuario que llama a la accion, restricciones de arcanas a mostrar
def create_arcanas_buttons(bot, game, action, uid, restrict = []):	
	#(-?[0-9]*)\*([A-Za-z]*)ArcanaAR\*(.*)\*(-?[0-9]*)
	#"Elige una Arcana:"
	btns = []
	i = 0
	for arcana_on_table in game.board.state.arcanasOnTable:
		if arcana_on_table["Título"] not in restrict:
 			btns.append([game.board.create_arcana_button(
				game.cid, arcana_on_table, i, comando_callback = "{}ArcanaAC".format(action))])
		i += 1
	# Agrego boton cancelar
	datos = str(game.cid) + "*{}ArcanaAC*Cancelar*".format(action) + str(-1)
	btns.append([InlineKeyboardButton("Cancelar", callback_data=datos)])
	return InlineKeyboardMarkup(btns)

# Crea los botones de fate de una arcana
def create_fate_buttons(bot, game, action, uid, arcana, arcana_index, greater_than, lower_than):	
	#(-?[0-9]*)\*([A-Za-z]*)FateAR\*(.*)\*(-?[0-9]*)
	#"Elige una Arcana:"
	btns = []
	fate_index = 0
	for fate_token in arcana['tokens']:
		if greater_than < int(fate_token["Texto"]) < lower_than:
			txtBoton = fate_token["Texto"]
			datos = "{}*{}FateAC*{}*{}".format(game.cid, action, fate_index, arcana_index)
			log.info("Datos: {}".format(datos))
			btns.append([InlineKeyboardButton(txtBoton, callback_data=datos)])
		fate_index += 1
	# Agrego boton cancelar
	datos = "{}*{}FateAC*-1*-1".format(game.cid, action)
	btns.append([InlineKeyboardButton("Cancelar", callback_data=datos)])
	return InlineKeyboardMarkup(btns)


def repetir_action(bot, game, uid):
	log.info('repetir_action called')
	# Verifico que el jugador no haya puesto en la arcana adivinar, sino
	game.board.state.extraGuess += 1
	game.history.append("Ahora pueden adivinar {} numeros.".format(game.board.state.extraGuess+1))
	return 1		

def action_123(bot, game, uid):
	log.info('action_123 called')
	fate_quedaba = game.board.state.active_player.fateTokens[0]
	msg = ""
	if int(fate_quedaba["Texto"]) in [1, 2, 3]:
		msg = f"*SI*, el destino restante de {game.board.state.active_player.name} es 1, 2 o 3"
	else:
		msg = f"*NO*, el destino restante de {game.board.state.active_player.name} no es 1, 2 o 3"
	game.history.append(msg)
	bot.send_message(game.cid, msg, parse_mode=ParseMode.MARKDOWN)
	return 1

def action_147(bot, game, uid):
	log.info('action_147 called')
	fate_quedaba = game.board.state.active_player.fateTokens[0]
	msg = ""
	if int(fate_quedaba["Texto"]) in [1, 4, 7]:
		msg = f"*SI*, el destino restante de {game.board.state.active_player.name} es 1, 4 o 7"
	else:
		msg = f"*NO*, el destino restante de {game.board.state.active_player.name} no es 1, 4 o 7"
	game.history.append(msg)
	bot.send_message(game.cid, msg, parse_mode=ParseMode.MARKDOWN)
	return 1

def action_345(bot, game, uid):
	log.info('action_345 called')
	fate_quedaba = game.board.state.active_player.fateTokens[0]
	msg = ""
	if int(fate_quedaba["Texto"]) in [3, 4, 5]:
		msg = f"*SI*, el destino restante de {game.board.state.active_player.name} es 3, 4 o 5"
	else:
		msg = f"*NO*, el destino restante de {game.board.state.active_player.name} no es 3, 4 o 5"
	game.history.append(msg)
	bot.send_message(game.cid, msg, parse_mode=ParseMode.MARKDOWN)
	return 1

def action_567(bot, game, uid):
	log.info('action_567 called')
	fate_quedaba = game.board.state.active_player.fateTokens[0]
	msg = ""
	if int(fate_quedaba["Texto"]) in [5, 6, 7]:
		msg = f"*SI*, el destino restante de *{game.board.state.active_player.name}* es 5, 6 o 7"
	else:
		msg = f"*NO*, el destino restante de *{game.board.state.active_player.name}* no es 5, 6 o 7"
	game.history.append(msg)
	bot.send_message(game.cid, msg, parse_mode=ParseMode.MARKDOWN)
	return 1

def dentroDe2_action(bot, game, uid):
	log.info('dentroDe2_action called')
	fate_quedaba = int(game.board.state.active_player.fateTokens[0]["Texto"])
	last_chosen_fate = int(game.board.state.active_player.last_chosen_fate["Texto"])
	msg = ""
	if abs(fate_quedaba-last_chosen_fate) in [1,2]:
		msg = f"*SI*, el destino restante de *{game.board.state.active_player.name}* está dentro de 2"
	else:
		msg = f"*NO*, el destino restante de *{game.board.state.active_player.name}* no está dentro de 2"
	game.history.append(msg)
	bot.send_message(game.cid, msg, parse_mode=ParseMode.MARKDOWN)
	return 1

# Acciones que se realizan al usar las fadded
def can_use_fadded(bot, game, uid, arcana):
	# Detecto el timing por el texto de la carta
	texto = arcana["Texto reverso"]
	titulo = arcana["Título reverso"]
	# Si es true es jugable antes de destino, sino prediccion
	destino = True if "de jugar" in texto else False
	# Si es true es antes, sino despues
	antes = True if "Antes de" in texto else False
	# Si es true la puede usar el jugador activo, sino el grupo
	jugador_activo = True if "el jugador activo" in texto else False	
	# Si es antes de poner destino el estado debe ser Jugar Fate, sino Predecir
	#log.info('destino: {}, antes: {}, Req jugador_activo: {}, Es el jugador activo?: {}'.format(destino, antes, jugador_activo, (uid==game.board.state.active_player.uid)))
	
	# VErifico si es el jugador correcto el que ejecuta 
	if (jugador_activo and not (uid==game.board.state.active_player.uid)) or (
		(not jugador_activo) and (uid==game.board.state.active_player.uid)):
		return False
	
	# Verifico que sea en la fase correcta.
	if antes and destino and game.board.state.fase_actual == "Jugar Fate":
		return True
	elif ((not antes) or (not destino)) and game.board.state.fase_actual == "Predecir":
		return True
	return False		
