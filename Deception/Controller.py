#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Leviatas"

import json
import logging as log
import random
import re
import math
from random import randrange
from time import sleep
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.ext import (CallbackContext)
from Utils import get_game, save, simple_choose_buttons
from Constants.Config import ADMIN
import copy

from Deception.Constants.Cards import playerSets, modules, clues, means, FORENSIC_CARDS
from Deception.Boardgamebox.Game import Game
from Deception.Boardgamebox.Player import Player
from Deception.Boardgamebox.Board import Board
import GamesController

import datetime

##
#
# Beginning of round
#
##
def init_game(bot, game):
	log.info("Entro a init de Deception")	
	
	# Create user to test functionality
	if game.is_debugging:
		for i in range(11):
			game.add_player(i, "Dummy {}".format(i))


	# SE comienza eligiendo el diccionario antes de que se elija al mayor
	call_dicc_buttons(bot, game)

'''	
def start_next_round(bot, game):
	bot.send_message(game.cid, "Finaliza ronda y comienza otra", ParseMode.MARKDOWN)
	start_round(bot, game)
'''

def call_dicc_buttons(bot, game):
	opciones_botones = { "facil" : "Facil", "medio" : "Medio", "dificil" : "Difícil"}
	simple_choose_buttons(bot, game.cid, 1234, game.cid, "choosediffDC", "Elija una dificultad para jugar", opciones_botones)


# Mix and send roles, inform about them.
def night_phase(bot, game):
	dificultad = game.configs['dificultad']
	player_number = len(game.playerlist)

	inform_players(bot, game, game.cid, player_number)	
	#log.info(game.board)
	game.shuffle_player_sequence()

	# Pongo al mayor al principio de la lista.
	jugadores = game.player_sequence
	jugadores.insert(0, jugadores.pop(jugadores.index(game.board.state.forense)))

	game.board.state.player_counter = 0
	msn = """*Bienvenido a Deception.*
*Objetivo team policia:* Encontrar al asesino, su medio y su pista vital.

*Objetivo team asesino:* Evitar que se encuentre el asesino, su medio y pista vital."""
	bot.send_message(game.cid, msn, ParseMode.MARKDOWN)
	

	# Reparto cartas
	give_players_means_evidence(bot, game, dificultad)
	# Pregunto al asesino 
	ask_choose_mean_evidence(bot, game, dificultad)
	game.board.print_board(bot, game)

def give_players_means_evidence(bot, game, dificultad):
	log.info('give_players_means_evidence called')
	posible_means = means.copy()
	posible_clues = clues.copy()

	random.shuffle(posible_means)
	random.shuffle(posible_clues)
	i= 0
	
	log.info(dificultad)
	
	cantidad = 5 if dificultad == "dificil" else (3 if dificultad == "facil" else 4)
	for player in game.playerlist.values():	
		# Ignoro al forense ya que el no recibe cartas
		if player.is_forense():
			continue
		player.clues = posible_clues[i : i+cantidad]
		player.means = posible_means[i : i+cantidad]
		i += cantidad
		msg = player.get_str_means_clues()
		send_message(bot, game, player, msg)

def ask_choose_mean_evidence(bot, game, opcion):
	log.info('ask_choose_mean_evidence called')
	# Si vengo de un partido anterior agrego los descartes de la partida anterior.	
	asesino = game.board.state.asesino

	dict_motivo = {}
	for i in range(len(asesino.means)):
		dict_motivo[i] = asesino.means[i]
	
	dict_pista = {}
	for i in range(len(asesino.clues)):
		dict_pista[i] = asesino.clues[i]

	
	msg_medio = "Partida en el grupo *{}*\nElegi tu medio de asesinato".format(game.groupName)
	msg_pista = "Partida en el grupo *{}*\nElegi tu pista vital del asesinato".format(game.groupName)
	simple_choose_buttons(bot, game.cid, asesino.uid, asesino.uid, "choosemotivoDC", msg_medio, dict_motivo)
	simple_choose_buttons(bot, game.cid, asesino.uid, asesino.uid, "choosepistaDC", msg_pista, dict_pista)

def continue_night_phase(bot, game):
	log.info('continue_night_phase called')
	# Si hay complice le digo quien es el asesino y sus objetos correspondientes.
	inform_forense_testigo_complice(bot, game)
	forense_choose_location(bot, game)

def forense_choose_location(bot, game):
	localizaciones = {}
	msg_descrp_loca = "Partida en el grupo *{}*\n*Elija una localización:*\n".format(game.groupName)
	for nombre, valores in FORENSIC_CARDS["localization"].items():
		localizaciones[nombre] = nombre
		msg_descrp_loca += "*{}*: {}\n".format(nombre, ', '.join(str(list(x.keys())[0]) for x in [x for x in valores.values()]))
	msg_descrp_loca = msg_descrp_loca[:-1]
	forense = game.board.state.forense
	simple_choose_buttons(bot, game.cid, forense.uid, forense.uid, "choosecontinueDayDC", msg_descrp_loca, localizaciones)

def get_inicial_cards(bot, game, localizacion):
	game.board.state.forensic_cards.append({ "Causa de la muerte" :  copy.deepcopy(FORENSIC_CARDS["causa de la muerte"])})
	game.board.state.forensic_cards.append({ localizacion : copy.deepcopy(FORENSIC_CARDS["localization"][localizacion]) })
	# Randomly get 4 scene cards
	# Set 
	game.board.state.scene_event_cards = [nombre for nombre, valores in FORENSIC_CARDS["scene"].items()]
	scene_event_cards = game.board.state.scene_event_cards
	for x in range(4):
		random_index = randrange(len(scene_event_cards))
		scene_desc = scene_event_cards.pop(random_index)
		game.board.state.forensic_cards.append({ scene_desc : copy.deepcopy(FORENSIC_CARDS["scene"][scene_desc]) })
	# Que el forense elija la primera carta.	
	start_round(bot, game)

def choose_forensic_card_menu(bot, game, check_has_bullet = True, only_scenes = False):
	# Si esta en la fase evidence_collection cambio el texto que muestro.
	fase_actual = game.board.state.fase_actual
	msg_descrp_loca = "*Elija una carta donde poner la BALA*\n" if fase_actual != "evidence_collection" else "*Elija carta para REEMPLAZAR.*\n"
	cards = {}
	for idx, card in enumerate(game.board.state.forensic_cards):
		for nombre, valores in card.items():
			# Solo las que no tienen balas o que no se verifique bala.
			if not any(x for x in valores.values() if list(x.items())[0][1]) or not check_has_bullet:
				if not only_scenes or idx not in [0, 1]:
					cards[idx] = nombre
	msg_descrp_loca += game.board.get_forensic_cards_description(True, check_has_bullet, only_scenes)
	forense = game.board.state.forense
	simple_choose_buttons(bot, game.cid, forense.uid, forense.uid, "chooseforensicDC", msg_descrp_loca, cards)

def choose_forensic_card_detail_menu(bot, game, card_index):
	msg_descrp_detail = "*Elija una carta donde poner la bala*\n"
	cards_detail = {}
	for nombre, valor in list(game.board.state.forensic_cards[card_index].values())[0].items():
		indices = "{}_{}".format(card_index, nombre)
		cards_detail[indices] = list(valor.keys())[0]
		msg_descrp_detail += "*{}*: {}\n".format(nombre, list(valor.keys())[0])
	msg_descrp_detail = msg_descrp_detail[:-1]
	cards_detail["Volver"] = "🔙 Volver"
	forense = game.board.state.forense
	simple_choose_buttons(bot, game.cid, forense.uid, forense.uid, "chooseforensicdetailDC", msg_descrp_detail, cards_detail)


# Relacionado a todo lo que es informar roles, medios y pistas
def inform_forense_testigo_complice(bot, game):
	asesino = game.board.state.asesino
	forense = game.board.state.forense
	msg = "El asesino es *{}*. Su pista clave es *{}* y su medio es *{}*".format(asesino.name, asesino.clue, asesino.mean)
	send_message(bot, game, forense, msg)
	if game.get_complice():
		complice = game.get_complice()
		send_message(bot, game, complice, msg)
		msg = "Asesino, el complice es *{}*".format(complice.name)
		send_message(bot, game, asesino, msg)
	if game.get_testigo():
		testigo = game.get_testigo()
		msg = "Forense, *el testigo* es: *{}*".format(testigo.name)
		send_message(bot, game, forense, msg)
		# Hago random a quien muestro primero al testigo para que no haya una seguridad
		zar  = random.randint(1,2)
		if zar == 1:
			msg = "Los sospechosos son: *{}* *{}*".format(asesino.name, complice.name)
		else:
			msg = "Los sospechosos son: *{}* *{}*".format(complice.name, asesino.name)
		send_message(bot, game, testigo, msg)

def inform_players(bot, game, cid, player_number):
	log.info('inform_players called')	
		
	roles_posibles = list(playerSets[player_number]["afiliacion"])
	
	# Agrego roles de los modulos.
	# set_roles(bot, game, roles_posibles)

	# Mezclo los roles asi no tocan siempre los mismos
	# Mezclo con mismo random para que se mantenga los roles bien.
	random.shuffle(roles_posibles)

	bot.send_message(cid,"""Vamos a comenzar el juego con *{}* jugadores!
	{}
	Ve a nuestro chat privado y mira tu rol secreto!""".format(player_number, print_player_info(roles_posibles)), ParseMode.MARKDOWN)
	
	# Creo una lista unica para poder repartir los roles a partir de las key de los player list
	player_ids = list(game.playerlist.keys())
	# Lo mezclo y lo uso para pasar por todos los jugadores
	random.shuffle(player_ids)

	if game.is_debugging:
		text_adming_roles_posibles = ""
		for rol in roles_posibles:
			text_adming_roles_posibles += "({} : {})".format(rol[0], rol[1]) + " - "			
		bot.send_message(ADMIN[0], text_adming_roles_posibles[:-3], ParseMode.MARKDOWN)
	
	for uid in player_ids:
		player = game.playerlist[uid]
		random_index = randrange(len(roles_posibles))
		#log.info(str(random_index))
		rol = roles_posibles.pop(random_index)
		
		player.rol = rol[0]
		player.afiliacion = rol[1]
			
	# Despues de repartir los roles elijo al mayor al azar y lo asigno.
		
	game.board.state.forense = game.get_forense()
	game.board.state.asesino = game.get_asesino()
	for uid, player in game.playerlist.items():	
		msg = "Tu rol secreto es: {}\nTu afiliación es: {}.".format(player.rol, player.afiliacion)
		send_message(bot, game, player, msg)

def set_roles(bot, game, lista_a_modificar):
	# Me fijo en cada modulo que roles hay y de que afiliacion son, cambio uno por uno.
	for modulo in game.modulos:
		# Me fijo si el modulo incluye roles
		if "roles" in modules[modulo]:
			modulo_actual = modules[modulo]["roles"]
			if not modulo_actual == None:
				for afiliacion, rol in modules[modulo]["roles"].items():	
					# Obtiene el indice y modifica el elemento en la lista 
					indice = next((i for i, v in enumerate(lista_a_modificar) if v in afiliacion), -1)
					if indice == -1:
						bot.send_message(ADMIN[0], "Se quiso agregar un afiliacion (%s) y rol (%s), cuando no hay afiliaciones disponibles" % (afiliacion, rol))	
					else:
						lista_a_modificar[indice] = rol

def print_player_info(roles_posibles):
	roles = ""
	for rol in roles_posibles:
		roles += "Rol: *{}*, Afiliación *{}*\n".format(rol[0], rol[1])
	return "*Los roles posibles son:*\n{}".format(roles)
# End Metodos de configuracion / Inicio
# Despues del mayor vamos por el resto de los roles que actuan de noche.

def send_message(bot, game, player, msg):
	msg = "*Partida en grupo {}*\n{}".format(game.groupName, msg)
	if game.is_debugging:
		mensaje = msg  + " - Mensaje enviado a {}".format(player.name)
		bot.send_message(ADMIN[0], mensaje, ParseMode.MARKDOWN)
	else:		
		bot.send_message(player.uid, msg, ParseMode.MARKDOWN)

# list_total lista con todos los elementos
# list_a_restar Elementos a restar a list_total
def list_menos_list(list_total, list_a_restar):
	return [x for x in list_total if x not in list_a_restar]

def start_round(bot, game):
	# Se informa sobre el juego a los jugadores
	#bot.send_message(game.cid, "El forense {} ha elegido el lugar".format(helper.player_call(game.board.state.forense)), parse_mode=ParseMode.MARKDOWN)

	game.board.state.fase_actual = "choose_location"
	game.board.print_board(bot, game)
	msn = "Comiencen a desarrollar teorias mientras el forense elige donde poner sus balas."
	bot.send_message(game.cid, msn, ParseMode.MARKDOWN)
	save(bot, game.cid)
	# Dar menu al forense para que ponga una pista.
	game.board.state.check_has_bullet = True
	game.board.state.only_scenes = False
	choose_forensic_card_menu(bot, game)

def accuse(bot, game, uid):
	forense_uid = game.board.state.forense.uid
	for player in game.player_sequence:
		# No te podes acusar a vos mismo, ni al forense
		opciones_botones = { player.uid : player.name  for player in game.player_sequence if player.uid not in [uid, forense_uid] }
	opciones_botones["Volver"] = "🔙 Volver"
	simple_choose_buttons(bot, game.cid, uid, uid, "chooseAccuseDE", "¿Quien crees que es el asesino?", opciones_botones, False, 2)

def accuse_choose_clue(bot, game, accuser, accused):
	# Pongo el id del acusado
	accuser.accused_player = accused
	accuser.accused_mean = None
	accuser.accused_clue = None
	# Le mando los dos menues con las pistas y medios
	dict_motivo = {}
	for i in range(len(accused.means)):
		dict_motivo[i] = accused.means[i]
	
	dict_pista = {}
	for i in range(len(accused.clues)):
		dict_pista[i] = accused.clues[i]
	
	msg_medio = "Partida en el grupo *{}*\nElegi el medio de {} que sospechas".format(game.groupName, accused.name)
	msg_pista = "Partida en el grupo *{}*\nElegi la pista de {} que sospechas".format(game.groupName, accused.name)
	simple_choose_buttons(bot, game.cid, accuser.uid, accuser.uid, "choosemotivoDC", msg_medio, dict_motivo)
	simple_choose_buttons(bot, game.cid, accuser.uid, accuser.uid, "choosepistaDC", msg_pista, dict_pista)

def resolve_acusacion(bot, game, accuser):
	msg = "De repente el jugador *{}* se levanta y señala a *{}*.\nHas sido tú lo se por esta pista *{}* y que has usado este medio *{}*".format(accuser.name, accuser.accused_player.name, accuser.accused_clue, accuser.accused_mean)	
	bot.send_message(game.cid, msg, parse_mode=ParseMode.MARKDOWN)
	# accuser.accused_player.name, accuser.accused_clue, accuser.accused_mean)	
	if accuser.accused_player.is_accusation_true(accuser.accused_clue, accuser.accused_mean):
		end_game(bot, game)
	else:
		msg = "*El mudo forense niega con la cabeza. Has fallado {}.*".format(accuser.name)
		bot.send_message(game.cid, msg, parse_mode=ParseMode.MARKDOWN)

def end_game(bot, game):
	# Imprimo los jugadores y sus roles
	game.board.state.fase_actual = "Terminado"
	msn = "*Juego finalizado*"
	bot.send_message(game.cid, msn, ParseMode.MARKDOWN)	
	save(bot, game.cid)
	bot.send_message(game.cid, game.print_roles(), parse_mode=ParseMode.MARKDOWN)
	continue_playing(bot, game)

def continue_playing(bot, game):
	opciones_botones = { "Nuevo" : "Nuevo Partido con nuevos jugadores", "Mismo Diccionario" : "Mismos jugadores, mismo Diccionario", "Otro Diccionario" : "Mismos jugadores, diferente diccionario"}
	simple_choose_buttons(bot, game.cid, 1, game.cid, "chooseendDC", "¿Quieres continuar jugando?", opciones_botones, False, 1)

# Metodos de configuracion / Inicio
def configurar_partida(bot, game):
	try:
		# Metodo para configurar la partida actual
		strcid = str(game.cid)			
		btns = []
		for modulo in modules.keys():
			if modulo not in game.modulos:
				btns.append([InlineKeyboardButton(modulo, callback_data=strcid + "_moduloDC_" + modulo)])
		btns.append([InlineKeyboardButton("Finalizar Configuración", callback_data=strcid + "_modulo_" + "Fin")])
		modulosMarkup = InlineKeyboardMarkup(btns)
		bot.send_message(game.cid, 'Elija un modulo para agregar!', reply_markup=modulosMarkup)
	except AttributeError as e:
		log.error("incluir_modulo: " + str(e))
	except Exception as e:
		log.error("Unknown error: " + repr(e))
		log.exception(e)

def incluir_modulo(update: Update, context: CallbackContext):
	bot = context.bot
	
	log.info('incluir_modulo')
	log.info(update.callback_query.data)
	callback = update.callback_query
	regex = re.search("(-[0-9]*)_moduloDC_(.*)", callback.data)
	
	cid = int(regex.group(1))
	modulo_elegido = regex.group(2)
	
	log.info(modulo_elegido)
	
	try:
		game = get_game(cid)		
		# Si se ha terminado de configurar los modulos...		
		
		if modulo_elegido == "Fin":
			bot.edit_message_text("Gracias por configurar el juego.", cid, callback.message.message_id)
		else:
			game.modulos.append(modulo_elegido)
			bot.edit_message_text("Se ha incluido el modulo %s" % (modulo_elegido), cid, callback.message.message_id)
			configurar_partida(bot, game)
	except AttributeError as e:
		log.error("incluir_modulo: " + str(e))
	except Exception as e:
		log.error("Unknown error: " + repr(e))
		log.exception(e)


# Callbacks de los botones

def callback_finish_config_werewords(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_finish_config_Deception called')
	callback = update.callback_query
	#try:
	regex = re.search(r"(-[0-9]*)\*choosediffDC\*(.*)\*([0-9]*)", callback.data)
	cid, opcion, uid = int(regex.group(1)), regex.group(2), update.effective_user.id
	mensaje_edit = "Has elegido la dificultad: {0}".format(opcion)
	try:
		bot.edit_message_text(mensaje_edit, cid, callback.message.message_id)
	except Exception as e:
		bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)
		
	game = get_game(cid)
	game.configs['dificultad'] = opcion
	night_phase(bot, game)
		
	#except Exception as e:
	#	bot.send_message(ADMIN[0], 'No se ejecuto el comando debido a: '+str(e))
	#	bot.send_message(ADMIN[0], callback.data)

def callback_choose_motivo(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_choose_motivo called')
	callback = update.callback_query
	
	regex = re.search(r"(-[0-9]*)\*choosemotivoDC\*(.*)\*([0-9]*)", callback.data)
	cid, opcion, uid = int(regex.group(1)), regex.group(2), update.effective_user.id
	
	game = get_game(cid)
	jugador_ejecutor = game.playerlist[uid]
	asesino = game.board.state.asesino

	# Si el asesino ya eligio motivo entonces se usa para acusar
	if asesino.mean is None:
		
		asesino.mean = asesino.means[int(opcion)]
		mensaje_edit = "Partida en el grupo *{}*\n*Has elegido el medio: {}*".format(game.groupName, asesino.mean)
		try:
			bot.edit_message_text(mensaje_edit, cid, callback.message.message_id, parse_mode=ParseMode.MARKDOWN)
		except Exception as e:
			uid = ADMIN[0] if game.is_debugging else uid
			bot.edit_message_text(mensaje_edit, uid, callback.message.message_id, parse_mode=ParseMode.MARKDOWN)
						
		#game.configs['magicword'] = opcion
		
		if asesino.mean is not None and asesino.clue is not None:
			continue_night_phase(bot, game)
	else:
		accused = jugador_ejecutor.accused_player
		jugador_ejecutor.accused_mean = accused.means[int(opcion)]
		mensaje_edit = "Partida en el grupo *{}*\n*Has elegido el medio: {}*".format(game.groupName, jugador_ejecutor.accused_mean)
		uid = ADMIN[0] if game.is_debugging else uid
		bot.edit_message_text(mensaje_edit, uid, callback.message.message_id, parse_mode=ParseMode.MARKDOWN)
		if jugador_ejecutor.accused_mean is not None and jugador_ejecutor.accused_clue is not None:
			resolve_acusacion(bot, game, jugador_ejecutor)


def callback_choose_pista(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_choose_pista called')
	callback = update.callback_query
	
	regex = re.search(r"(-[0-9]*)\*choosepistaDC\*(.*)\*([0-9]*)", callback.data)
	cid, opcion, uid = int(regex.group(1)), regex.group(2), update.effective_user.id
	
	game = get_game(cid)
	jugador_ejecutor = game.playerlist[uid]
	asesino = game.board.state.asesino
	if asesino.clue is None:
		
		asesino.clue = asesino.clues[int(opcion)]
		mensaje_edit = "Partida en el grupo *{}*\n*Has elegido la pista: {}*".format(game.groupName, asesino.clue)
		try:
			bot.edit_message_text(mensaje_edit, cid, callback.message.message_id, parse_mode=ParseMode.MARKDOWN)
		except Exception as e:
			uid = ADMIN[0] if game.is_debugging else uid
			bot.edit_message_text(mensaje_edit, uid, callback.message.message_id, parse_mode=ParseMode.MARKDOWN)
				
		if asesino.mean is not None and asesino.clue is not None:
			continue_night_phase(bot, game)
	else:
		accused = jugador_ejecutor.accused_player
		jugador_ejecutor.accused_clue = accused.clues[int(opcion)]
		mensaje_edit = "Partida en el grupo *{}*\n*Has elegido la pista: {}*".format(game.groupName, jugador_ejecutor.accused_clue)
		uid = ADMIN[0] if game.is_debugging else uid
		bot.edit_message_text(mensaje_edit, uid, callback.message.message_id, parse_mode=ParseMode.MARKDOWN)
		if jugador_ejecutor.accused_mean is not None and jugador_ejecutor.accused_clue is not None:
			resolve_acusacion(bot, game, jugador_ejecutor)


def callback_choose_continue(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_choose_continue called')
	callback = update.callback_query
	try:
		regex = re.search(r"(-?[0-9]*)\*choosecontinueDayDC\*(.*)\*(-?[0-9]*)", callback.data)
		cid, localizacion, uid = int(regex.group(1)), regex.group(2), update.effective_user.id

		game = get_game(cid)
		jugador_ejecutor = game.playerlist[uid]

		'''
		valid_callback = game.validate_call_choose_continue(jugador_ejecutor)
		if not valid_callback:
			mensaje_edit = "No puedes o no es el momento para usar esta botonera"
			bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)
			return
		'''
		mensaje_edit = "*Haz elegido la localización {}*".format(localizacion)
		try:
			bot.edit_message_text(mensaje_edit, cid, callback.message.message_id, parse_mode=ParseMode.MARKDOWN)
		except Exception as e:
			bot.edit_message_text(mensaje_edit, uid, callback.message.message_id, parse_mode=ParseMode.MARKDOWN)
		
		save(bot, game.cid)

		get_inicial_cards(bot, game, localizacion)
		#continue_night_phase(bot, game)	

	except Exception as e:
		bot.send_message(ADMIN[0], 'No se ejecuto el comando debido a: '+str(e))
		bot.send_message(ADMIN[0], callback.data)

def callback_choose_forensic(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_choose_continue called')
	callback = update.callback_query
	try:
		regex = re.search(r"(-?[0-9]*)\*chooseforensicDC\*(.*)\*(-?[0-9]*)", callback.data)
		cid, card_index, uid = int(regex.group(1)), int(regex.group(2)), update.effective_user.id

		game = get_game(cid)
		jugador_ejecutor = game.playerlist[uid]

		'''
		valid_callback = game.validate_call_choose_continue(jugador_ejecutor)
		if not valid_callback:
			mensaje_edit = "No puedes o no es el momento para usar esta botonera"
			bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)
			return
		'''
		current_cards = game.board.state.forensic_cards
		carta = list(current_cards[card_index].keys())[0]

		mensaje_edit = "Haz elegido la carta *{}*".format(carta)
		try:
			bot.edit_message_text(mensaje_edit, cid, callback.message.message_id, parse_mode=ParseMode.MARKDOWN)
		except Exception as e:
			bot.edit_message_text(mensaje_edit, uid, callback.message.message_id, parse_mode=ParseMode.MARKDOWN)
		
		save(bot, game.cid)

		fase_actual = game.board.state.fase_actual
		# Si es
		if fase_actual != "evidence_collection":
			choose_forensic_card_detail_menu(bot, game, card_index)
		else:
			# Reemplazo la carta elegida por la nueva.
			game.board.state.forensic_cards[card_index] = game.board.state.new_scene_event_card.pop()
			# Le doy el menu al forense para poner la bala
			game.board.state.check_has_bullet = True
			game.board.state.only_scenes = True
			game.board.state.fase_actual = "set_new_evidence"
			save(bot, game.cid)	
			choose_forensic_card_menu(bot, game, game.board.state.check_has_bullet, game.board.state.only_scenes)			

	except Exception as e:
		bot.send_message(ADMIN[0], 'No se ejecuto el comando debido a: '+str(e))
		bot.send_message(ADMIN[0], callback.data)
		
def callback_choose_forensic_detail(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_choose_continue called')
	callback = update.callback_query
	try:
		regex = re.search(r"(-?[0-9]*)\*chooseforensicdetailDC\*(.*)\*(-?[0-9]*)", callback.data)
		
		cid, card_index, uid = int(regex.group(1)), regex.group(2), update.effective_user.id
		

		game = get_game(cid)
		jugador_ejecutor = game.playerlist[uid]

		'''
		valid_callback = game.validate_call_choose_continue(jugador_ejecutor)
		if not valid_callback:
			mensaje_edit = "No puedes o no es el momento para usar esta botonera"
			bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)
			return
		'''

		current_cards = game.board.state.forensic_cards
		
		if (card_index == "Volver"):
			mensaje_edit = "Volviendo atras."
			try:
				bot.edit_message_text(mensaje_edit, cid, callback.message.message_id, parse_mode=ParseMode.MARKDOWN)
			except Exception as e:
				bot.edit_message_text(mensaje_edit, uid, callback.message.message_id, parse_mode=ParseMode.MARKDOWN)
				choose_forensic_card_menu(bot, game, game.board.state.check_has_bullet, game.board.state.only_scenes)
			return

		indices = card_index.split('_')

		carta = list(current_cards[int(indices[0])].keys())[0]
		#log.info(indices)
		#log.info(current_cards)
		#log.info(list(list(current_cards[int(indices[0])].values())[0][indices[1]].keys())[0])

		try:
			detalle = list(list(current_cards[int(indices[0])].values())[0][int(indices[1])].keys())[0]
		except Exception as e:
			detalle = list(list(current_cards[int(indices[0])].values())[0][indices[1]].keys())[0]

		mensaje_edit = "Haz elegido la carta *{}* y el detalle *{}*".format(carta, detalle)
		try:
			bot.edit_message_text(mensaje_edit, cid, callback.message.message_id, parse_mode=ParseMode.MARKDOWN)
		except Exception as e:
			bot.edit_message_text(mensaje_edit, uid, callback.message.message_id, parse_mode=ParseMode.MARKDOWN)
		
		try:
			list(current_cards[int(indices[0])].values())[0][int(indices[1])][detalle] = True
		except Exception as e:
			list(current_cards[int(indices[0])].values())[0][indices[1]][detalle] = True
		
		# Disminuyo en 1 las balas
		jugador_ejecutor.bullet_marker -= 1

		save(bot, game.cid)

		bot.send_message(game.cid, "*El forense ha puesto una bala en la carta {} en la posicion {}*".format(carta, detalle), ParseMode.MARKDOWN)

		# Muestro el cambio
		bot.send_message(game.cid, game.board.get_forensic_cards_description(True, False, False), ParseMode.MARKDOWN)
		# Le doy el menu al forense para que continue.
		if jugador_ejecutor.bullet_marker > 0:
			choose_forensic_card_menu(bot, game)
		else:
			bot.send_message(game.cid, "*El forense ha puesto su ultima bala*\nCuando quieras hacen exposicion y /newevidence", ParseMode.MARKDOWN)

		#continue_night_phase(bot, game)	

	except Exception as e:
		bot.send_message(ADMIN[0], 'No se ejecuto el comando debido a: '+str(e))
		bot.send_message(ADMIN[0], callback.data)
		raise e

def callback_accuse(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('chooseAccuseDE called')
	callback = update.callback_query
	
	regex = re.search(r"(-[0-9]*)\*chooseAccuseDE\*(.*)\*([0-9]*)", callback.data)
	cid, opcion, uid = int(regex.group(1)), regex.group(2), update.effective_user.id	
	game = get_game(cid)

	if (opcion == "Volver"):
		mensaje_edit = "Volviendo atras."
		bot.edit_message_text(mensaje_edit, uid, callback.message.message_id, parse_mode=ParseMode.MARKDOWN)
		accuse(bot, game, uid)
		return

	jugador_elegido = game.playerlist[int(opcion)]
	jugador_ejecutor = game.playerlist[uid]

	mensaje_edit = "Partida en el grupo *{}*\n*Has elegido para accusar a: {}*".format(game.groupName, jugador_elegido.name)
	
	try:
		bot.edit_message_text(mensaje_edit, cid, callback.message.message_id, parse_mode=ParseMode.MARKDOWN)
	except Exception as e:
		uid = ADMIN[0] if game.is_debugging else uid
		bot.edit_message_text(mensaje_edit, uid, callback.message.message_id, parse_mode=ParseMode.MARKDOWN)
	
	accuse_choose_clue(bot, game, jugador_ejecutor, jugador_elegido)

def callback_finish_game_buttons(update: Update, context: CallbackContext):
	bot = context.bot
	callback = update.callback_query
	try:		
		log.info('callback_finish_game_buttons called: %s' % callback.data)	
		regex = re.search(r"(-[0-9]*)\*chooseendDC\*(.*)\*([0-9]*)", callback.data)
		cid, strcid, opcion, uid, struid = int(regex.group(1)), regex.group(1), regex.group(2), int(regex.group(3)), regex.group(3)
		mensaje_edit = "Has elegido: {0}".format(opcion)
		try:
			bot.edit_message_text(mensaje_edit, cid, callback.message.message_id)
		except Exception as e:
			bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)				
		
		game = get_game(cid)
		
		# Obtengo el diccionario actual, primero casos no tendre el config y pondre el community
		try:
			dicc = game.configs.get('dificultad','facil')
		except Exception as e:
			dicc = 'facil'
		
		# Obtengo datos de juego anterior		
		groupName = game.groupName
		tipojuego = game.tipo
		modo = game.modo
		descarte = game.board.discards
		# Dependiendo de la opcion veo que como lo inicio
		# Copio los jugadores
		playerlist = {}
		for uid, player in game.playerlist.items():
			playerlist[uid] = Player(player.name, uid)
		# Si estaba debugeando, sigo debugeando		
		is_debugging = game.is_debugging

		# Creo nuevo juego
		game = Game(cid, uid, groupName, tipojuego, modo)
		# Si estaba debugeando, sigo debugeando.
		game.is_debugging = is_debugging

		GamesController.games[cid] = game
		# Guarda los descartes en configs para asi puedo recuperarlos
		game.configs['discards'] = descarte
		if opcion == "Nuevo":
			bot.send_message(cid, "Cada jugador puede unirse al juego con el comando /join.\nEl iniciador del juego (o el administrador) pueden unirse tambien y escribir /startgame cuando todos se hayan unido al juego!")			
			return
				
		# Solo la opcion nuevo no mete a los jugadores anteriores
		game.playerlist = playerlist
		# Creo el tablero
		player_number = len(game.playerlist)
		game.board = Board(player_number, game)	

		if opcion == "Mismo Diccionario":
			game.configs['dificultad'] = dicc
			night_phase(bot, game)
			return
		elif opcion == "Otro Diccionario":
			init_game(bot, game)
			
	except Exception as e:
		bot.send_message(ADMIN[0], 'No se ejecuto el comando debido a: '+str(e))
		bot.send_message(ADMIN[0], callback.data)