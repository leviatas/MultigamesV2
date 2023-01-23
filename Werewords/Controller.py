#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Leviatas"

import json
import logging as log
import random
import re
import math
from random import randrange, shuffle
from time import sleep
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.ext import (CallbackContext)

from Utils import (player_call, showFirstLetter, next_player_certain_player, previous_player_after_certain_player, simple_choose_buttons, get_game, save)
from Constants.Config import ADMIN

from Werewords.Constants.Cards import playerSets
from Werewords.Constants.Cards import modules
from Werewords.Boardgamebox.Game import Game
from Werewords.Boardgamebox.Player import Player
from Werewords.Boardgamebox.Board import Board
import GamesController

import datetime

##
#
# Beginning of round
#
##
def init_game(bot, game):
	log.info("Entro a init de Werewords")	
	
	# Create user to test functionality
	if game.is_debugging:
		for i in range(19):
			game.add_player(i, "Dummy {}".format(i))


	# SE comienza eligiendo el diccionario antes de que se elija al mayor
	call_dicc_buttons(bot, game)

'''	
def start_next_round(bot, game):
	bot.send_message(game.cid, "Finaliza ronda y comienza otra", ParseMode.MARKDOWN)
	start_round(bot, game)
'''

def call_dicc_buttons(bot, game):
	opciones_botones = { "facil" : "Facil", "original" : "Español Nuestro", "community" : "Español Community", "edespañola"  : "Original Ed Española"}
	simple_choose_buttons(bot, game.cid, 1234, game.cid, "choosediccWW", "¿Elija un diccionario para jugar?", opciones_botones)

def callback_finish_config_werewords(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_finish_config_werewords called')
	callback = update.callback_query
	#try:
	regex = re.search("(-[0-9]*)\*choosediccWW\*(.*)\*([0-9]*)", callback.data)
	cid, strcid, opcion, uid, struid = int(regex.group(1)), regex.group(1), regex.group(2), int(regex.group(3)), regex.group(3)
	mensaje_edit = "Has elegido el diccionario: {0}".format(opcion)
	try:
		bot.edit_message_text(mensaje_edit, cid, callback.message.message_id)
	except Exception as e:
		bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)
		
	game = get_game(cid)
	game.configs['diccionario'] = opcion
	night_phase(bot, game)
		
	#except Exception as e:
	#	bot.send_message(ADMIN[0], 'No se ejecuto el comando debido a: '+str(e))
	#	bot.send_message(ADMIN[0], callback.data)

# Mix and send roles, inform about them.
def night_phase(bot, game):
	diccionario = game.configs['diccionario']
	player_number = len(game.playerlist)

	inform_players(bot, game, game.cid, player_number)	
	#log.info(game.board)
	#log.info("len(games) Command_startgame: " + str(len(GamesController.games)))
	game.shuffle_player_sequence()

	# Pongo al mayor al principio de la lista.
	jugadores = game.player_sequence
	jugadores.insert(0, jugadores.pop(jugadores.index(game.board.state.mayor)))

	game.board.state.player_counter = 0
	msn = """*Bienvenido a Werewords.*
*Objetivo Aldeanos:* Adivinar la palabra al finalizar las preguntas al Mayor y que los hombres lobos no adivinen la adivina

*Objetivo hombre Lobos:* Evitar que se adivine la palabra al finalizar las preguntas al mayor y que no los elijan."""
	bot.send_message(game.cid, msn, ParseMode.MARKDOWN)
	ask_mayor_for_magic_word(bot, game, diccionario)

# Metodos de configuracion / Inicio
def configurar_partida(bot, game):
	try:
		# Metodo para configurar la partida actual
		strcid = str(game.cid)			
		btns = []
		for modulo in modules.keys():
			if modulo not in game.modulos:
				btns.append([InlineKeyboardButton(modulo, callback_data=strcid + "_moduloWW_" + modulo)])
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
	regex = re.search("(-[0-9]*)_moduloWW_(.*)", callback.data)
	
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

def inform_badguys(bot, game):
	log.info('inform_badguys called')
	werewolfs = game.get_badguys()
	secuaces = game.get_minions()

	for uid, player in game.playerlist.items():
		texto_lobos = ""
		for f in werewolfs:				
			if f.uid != uid:
				texto_lobos += f.name					
				texto_lobos += ", "
		texto_lobos = texto_lobos[:-2]
		afiliacion = player.afiliacion		
		# Si es del equipo werewolf
		if player.is_werewolf_team():
			# Si es hombre lobo y hay otros hombre lobos		
			if player.is_werewolf() and len(werewolfs) > 1:
				msg = "Tus compañeros hombres lobo son: {}".format(texto_lobos)
				send_message(bot, game, player, msg)
			elif player.is_minion():
				msg = "Tus compañeros hombres lobo son: {}".format(texto_lobos)
				send_message(bot, game, player, msg)
				# Caso especial del dopple si se convierte en Secuaz se ven entre ellos.
				if len(secuaces) > 1:
					texto_secuaces = ""
					for f in secuaces:				
						if f.uid != uid:
							texto_secuaces += f.name
					msg = "Tu compañero secuaz es: {}".format(texto_secuaces)
					send_message(bot, game, player, msg)
		else:
			log.error("inform_badguys: no se que hacer con la afiliacion: {}".format(afiliacion))

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
	if game.is_debugging:
		vidente = game.get_vidente()
		vidente.is_mayor = True
	else:
		random_index = randrange(len(player_ids))
		random_player_id = player_ids[random_index]
		random_player = game.playerlist[random_player_id] 
		random_player.is_mayor = True
	
	game.board.state.mayor = game.get_mayor()
	for uid, player in game.playerlist.items():	
		mayor_txt = "\n*ERES EL MAYOR*" if player.is_mayor else ""
		msg = "Tu rol secreto es: {}\nTu afiliación es: {}.{}".format(player.rol, player.afiliacion, mayor_txt)
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

def ask_mayor_for_magic_word(bot, game, opcion):
	log.info('ask_mayor_for_magic_word called')
	# Si vengo de un partido anterior agrego los descartes de la partida anterior.	
	if game.configs.get('discards', None):
		game.board.discards = game.configs.get('discards')
		del game.configs['discards']
	url_palabras_posibles = '/Werewords/txt/spanish-{0}.txt'.format(opcion)	
	with open(url_palabras_posibles, 'r') as f:
		palabras_posibles = f.readlines()
		palabras_posibles = [w.replace('\n', '') for w in palabras_posibles]
		palabras_posibles_no_repetidas = list_menos_list(palabras_posibles, game.board.discards)
		# Si no hay palabra posible no repetidas para jugar mezclo todas las palabras posibles
		if len(palabras_posibles_no_repetidas) < 2:
			# Quedo bien 
			game.board.discards = []
			palabras_posibles_no_repetidas = palabras_posibles		
		shuffle(palabras_posibles_no_repetidas)
		game.board.cards = palabras_posibles_no_repetidas[0:2]		
		game.board.cards = [w.replace('\n', '') for w in game.board.cards]

	temp_dic = {}
	for card in game.board.cards:
		temp_dic[card] = card	
	player_mayor_id = ADMIN[0] if game.is_debugging else game.get_mayor().uid
	#log.info(temp_dic)
	simple_choose_buttons(bot, game.cid, player_mayor_id, player_mayor_id, "choosemagicwordWW", "¿Elija una palabra magica?", temp_dic)
	bot.send_message(game.cid, "Mayor {} tienes que elegir una palabra en nuestro privado.".format(player_call(game.get_mayor())), parse_mode=ParseMode.MARKDOWN)
	#simple_choose_buttons(bot, game.cid, 1234, game.cid, "choosemagicwordWW", "¿Elija una palabra magica?", temp_dic)
	
def callback_choose_magic_word(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_choose_magic_word called')
	callback = update.callback_query
	
	regex = re.search("(-[0-9]*)\*choosemagicwordWW\*(.*)\*([0-9]*)", callback.data)
	cid, opcion, uid = int(regex.group(1)), regex.group(2), int(regex.group(3)),
	mensaje_edit = "Has elegido la palabra: {0}".format(opcion)
	game = get_game(cid)
	try:
		bot.edit_message_text(mensaje_edit, cid, callback.message.message_id)
	except Exception as e:
		uid = ADMIN[0] if game.is_debugging else uid
		bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)
		
	
	#game.configs['magicword'] = opcion
	continue_night_phase(bot, game, opcion)
	
# Despues del mayor vamos por el resto de los roles que actuan de noche.
def continue_night_phase(bot, game, opcion):
	log.info('continue_night_phase called')
	# pongo la palabra magica en el tablero.
	game.board.magic_word = opcion
	
	dople = game.get_rol("Dopleganger")
	if dople:
		inform_dople(bot, game)
	else:
		after_dople(bot, game)		

def after_dople(bot, game):
	inform_seer(bot, game)
	inform_fortune_teller(bot, game)
	inform_aprentice(bot, game)	
	inform_oracle(bot, game)	
	inform_masons(bot, game)
	cosa = game.get_rol("Cosa")
	if cosa:
		inform_thing(bot, game)
	else:
		after_thing(bot, game)

def after_thing(bot, game):
	inform_wolfs(bot, game)	
	start_round(bot, game)

def inform_dople(bot, game):
	# TODO Aca Elijo al azar un jugador que no sea el dopple y obtiene el rol de ese personaje.
	dople = game.get_rol("Dopleganger")

	opciones_botones = { player.uid : player.name  for player in game.player_sequence if player.uid != dople.uid }
	simple_choose_buttons(bot, game.cid, dople.uid, dople.uid, "choosedopleWW", "¿A quien quieres copiar?", opciones_botones, False, 2)
	'''
	random_player_to_duplicate = helper.choose_random(game.player_sequence, [dople])
	dople.dople_rol = random_player_to_duplicate.rol
	dople.dople_afiliacion = random_player_to_duplicate.afiliacion
	msg = "Has duplicado al {} con afiliacion {}".format(dople.dople_rol, dople.dople_afiliacion)
	send_message(bot, game, dople, msg)
	'''

def callback_choose_dople(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_choose_dople called')
	callback = update.callback_query
	#try:
	regex = re.search("(-?[0-9]*)\*choosedopleWW\*(.*)\*(-?[0-9]*)", callback.data)
	cid, opcion, uid = int(regex.group(1)), regex.group(2), int(regex.group(3))

	game = get_game(cid)
	jugador_ejecutor = game.playerlist[uid]
	jugador_elegido = game.playerlist[int(opcion)]

	valid_callback = game.validate_call_choose_poke(uid)
	if not valid_callback:
		mensaje_edit = "No puedes o no es el momento para usar esta botonera"
		bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)
		return

	mensaje_edit = "Has duplicado al jugador: {0}".format(jugador_elegido.name)
	try:
		bot.edit_message_text(mensaje_edit, cid, callback.message.message_id)
	except Exception as e:
		bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)
	
	dople = game.get_rol("Dopleganger")
	dople.dople_rol = jugador_elegido.rol
	dople.dople_afiliacion = jugador_elegido.afiliacion
	msg = "Has duplicado al *{}* con afiliacion *{}*".format(dople.dople_rol, dople.dople_afiliacion)
	send_message(bot, game, dople, msg)
	after_choose_dople_rol(bot, game)
	#save(bot, game.cid)		

	#except Exception as e:
	#	bot.send_message(ADMIN[0], 'No se ejecuto el comando en choosedopleWW debido a: '+str(e))
	#	bot.send_message(ADMIN[0], callback.data) 

def after_choose_dople_rol(bot, game):
	dople = game.get_rol("Dopleganger")
	
	# Acciones	
	#TODO Poner un timer para que haga de cosa el dopple
	bot.send_message(game.cid,"Esperamos a que el Dopleganger actue", ParseMode.MARKDOWN)
	
	#Hombre lobo se ve con ellos y la palabra
	#Minion se despierta con el minion y ve a los otros
	#Mason se muestra con ellos
	#Oraculo despierta con ella y se ven entre ellos.
	if dople.dople_rol == "Vidente":
		msg = "La palabra magica es: {}".format(game.board.magic_word)	
		send_message(bot, game, dople, msg)
	elif dople.dople_rol == "Adivinadora":
		first_letter_magic_word = showFirstLetter(game.board.magic_word)
		msg = "La palabra magica es: {}".format(first_letter_magic_word)	
		send_message(bot, game, dople, msg)
	elif dople.dople_rol == "Aprendiz":
		mayor = game.get_mayor()
		vidente = game.get_vidente()
		adivinadora = game.get_rol("Adivinadora")
		if mayor is vidente:
			msg = "La palabra magica es: *{}*".format(game.board.magic_word)
			game.board.state.aprendiz_vidente = True
			send_message(bot, game, dople, msg)
		elif mayor is adivinadora:
			first_letter_magic_word = showFirstLetter(game.board.magic_word)
			msg = "La palabra magica contiene: *{}*".format(first_letter_magic_word)
			game.board.state.aprendiz_adivinadora = True
			send_message(bot, game, dople, msg)
		else:
			msg = "*El mayor no es*: *vidente*"
			msg += ", *ni adivinadora*" if adivinadora else ""
			# De otra manera informo al aprendiz que el mayor no es la vidente y en caso de haber adivinadora, tampoco la adivinadora.
			send_message(bot, game, dople, msg)
	elif dople.dople_rol == "Cosa":
		bot.send_message(game.cid,"Eres la cosa!!!!", ParseMode.MARKDOWN)
		players = game.player_sequence
		next_player = next_player_certain_player(players, dople)
		previous_player = previous_player_after_certain_player(players, dople)
		poke_list = [next_player, previous_player]
		random_index = randrange(len(poke_list))
		#log.info(str(random_index))
		jugador_elegido = poke_list.pop(random_index)
		msg = "Has molestado al jugador: {0}".format(jugador_elegido.name)
		send_message(bot, game, dople, msg)
		msg = "El jugador *{}* te ha molestado, *es la COSA*!".format(dople.name)
		send_message(bot, game, jugador_elegido, msg)

	after_dople(bot, game)

def inform_wolfs(bot, game):
	# Se le muestra a los Hombre lobos los otros hombres lobos.
	inform_badguys(bot, game)
	
	msg = "La palabra magica es: *{}*".format(game.board.magic_word)
	# Informo a los hombres lobo respecto a la palabra magica()
	hombre_lobos = game.get_badguys()
	for hombre_lobo in hombre_lobos:
		send_message(bot, game, hombre_lobo, msg)

def inform_seer(bot, game):
	vidente = game.get_vidente()
	msg = "La palabra magica es: {}".format(game.board.magic_word)	
	send_message(bot, game, vidente, msg)

def inform_fortune_teller(bot, game):
	adivinadora = game.get_rol("Adivinadora")	
	# Hay aprendiz?
	if adivinadora:
		first_letter_magic_word = showFirstLetter(game.board.magic_word)
		msg = "La palabra magica es: {}".format(first_letter_magic_word)	
		send_message(bot, game, adivinadora, msg)		

def inform_aprentice(bot, game):
	aprendiz = game.get_rol("Aprendiz")
	if aprendiz:
		mayor = game.get_mayor()
		vidente = game.get_vidente()
		adivinadora = game.get_rol("Adivinadora")
		if mayor is vidente:
			msg = "La palabra magica es: *{}*".format(game.board.magic_word)
			game.board.state.aprendiz_vidente = True
			send_message(bot, game, aprendiz, msg)
		elif mayor is adivinadora:
			first_letter_magic_word = showFirstLetter(game.board.magic_word)
			msg = "La palabra magica contiene: *{}*".format(first_letter_magic_word)
			game.board.state.aprendiz_adivinadora = True
			send_message(bot, game, aprendiz, msg)
		else:
			msg = "*El mayor no es*: *vidente*"
			msg += ", *ni adivinadora*" if adivinadora else ""
			# De otra manera informo al aprendiz que el mayor no es la vidente y en caso de haber adivinadora, tampoco la adivinadora.
			send_message(bot, game, aprendiz, msg)

def inform_oracle(bot, game):
	oraculos = game.get_oracles()
	# Si hay oraculo
	if len(oraculos) > 0:
		vidente = game.get_vidente()
		aprendiz = game.get_rol("Aprendiz")	
		adivinadora = game.get_rol("Adivinadora")
		msg = "La vidente es *{}*".format(vidente.name)
		msg += "\nLa aprendiz es *{}*".format(aprendiz.name) if aprendiz else ""
		msg += "\nLa adivinadora es *{}*".format(adivinadora.name) if adivinadora else ""
		for oraculo in oraculos:
			send_message(bot, game, oraculo, msg)
		# Si el dopple es oraculo informo al otro oraculo.
		if len(oraculos) > 1:
			msg = "Hay dos oraculos y estos son: {} y {}".format(oraculos[0].name, oraculos[1].name)
			for oraculo in oraculos:
				send_message(bot, game, oraculo, msg)


def inform_masons(bot, game):
	masones = game.get_masones()	
	if len(masones) > 0:
		msg = "Los masones son: "		
		for mason in masones:
			msg += "{}, ".format(mason.name)
		msg = msg[:-2]
		for mason in masones:
			send_message(bot, game, mason, msg)				

def inform_thing(bot, game):
	cosa = game.get_rol("Cosa")
	
	# Busco mis compañeros de al lado y le doy opcion de que les haga un Poke.
	bot.send_message(game.cid, "*Esperemos a que la \"Cosa\" Golpee a un jugador al lado tuyo.*", ParseMode.MARKDOWN)
	players = game.player_sequence
	next_player = next_player_certain_player(players, cosa)
	previous_player = previous_player_after_certain_player(players, cosa)
	poke_list = {}
	poke_list[next_player.uid] = next_player.name
	poke_list[previous_player.uid] = previous_player.name
	simple_choose_buttons(bot, game.cid, cosa.uid, cosa.uid, "choosepokeWW", "¿A quien deseas molestar?", poke_list)

def callback_choose_poke(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_choose_vidente called')
	callback = update.callback_query
	try:
		regex = re.search("(-?[0-9]*)\*choosepokeWW\*(.*)\*(-?[0-9]*)", callback.data)
		cid, opcion, uid = int(regex.group(1)), regex.group(2), int(regex.group(3))

		game = get_game(cid)
		jugador_ejecutor = game.playerlist[uid]
		jugador_elegido = game.playerlist[int(opcion)]

		valid_callback = game.validate_call_choose_poke(uid)
		if not valid_callback:
			mensaje_edit = "No puedes o no es el momento para usar esta botonera"
			bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)
			return

		mensaje_edit = "Has molestado al jugador: {0}".format(jugador_elegido.name)
		try:
			bot.edit_message_text(mensaje_edit, cid, callback.message.message_id)
		except Exception as e:
			bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)
		
		msg = "El jugador *{}* te ha molestado, *es la COSA*!".format(jugador_ejecutor.name)
		send_message(bot, game, jugador_elegido, msg)
		after_thing(bot, game)
		#save(bot, game.cid)		

	except Exception as e:
		bot.send_message(ADMIN[0], 'No se ejecuto el comando debido a: '+str(e))
		bot.send_message(ADMIN[0], callback.data)

def send_message(bot, game, player, msg):
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
	bot.send_message(game.cid, "El Mayor {} ha elegido la palabra magica".format(player_call(game.get_mayor())), parse_mode=ParseMode.MARKDOWN)
	game.board.state.fase_actual = "preguntar"
	game.board.print_board(bot, game)	
	msn = """Hagan preguntas al Mayor con /ask PREGUNTA, el puede responder SI / NO / TAL VEZ / Muy CERCA *quedan {}* preguntas.
Mayor podes usar /toofar /soclose para usar MUY LEJOS y MUY CERCA sin necesidad de pregunta.

Si desean una partida con timer pongan /timer Para 8 minutos y 26 preguntas.""".format(game.board.state.preguntas_restantes)
	bot.send_message(game.cid, msn, ParseMode.MARKDOWN)	
	save(bot, game.cid)

def callback_ask(update: Update, context: CallbackContext):
	#(bot, update, chat_data, job_queue):
	bot = context.bot
	chat_data = context.chat_data
	job_queue = context.job_queue
	log.info('callback_choose_magic_word called')
	callback = update.callback_query
	uid = update.effective_user.id
	#try:
	regex = re.search("(-[0-9]*)\*askWW\*(.*)\*([0-9]*)", callback.data)
	cid, opcion, index = int(regex.group(1)), regex.group(2), int(regex.group(3)),
	
	game = get_game(cid)

	pregunta = game.board.state.preguntas_pendientes[index]
	
	if pregunta.respuesta is not None:
		bot.edit_message_text("Pregunta ya respondida", cid, callback.message.message_id, parse_mode=ParseMode.MARKDOWN)
		return
	
	if uid != game.board.state.mayor.uid and not game.is_debugging:
		jugador_presiono = game.playerlist[uid]
		bot.send_message(cid, "*{}* tu *NO* tienes que responder las preguntas!".format(jugador_presiono.name), parse_mode=ParseMode.MARKDOWN)
		return

	pregunta.respuesta = opcion.upper()
	pregunta_respuesta = "*{}: {}*".format(pregunta.pregunta, opcion.upper())

	if opcion == "Muy Lejos":
		game.board.state.muy_lejos = False
	if opcion == "Muy Cerca":
		game.board.state.muy_cerca = False
	if opcion == "Correcto":
		game.board.state.correcto = False

	mensaje_edit = "Gracias por responder"
	try:
		bot.edit_message_text(mensaje_edit, cid, callback.message.message_id, parse_mode=ParseMode.MARKDOWN)
	except Exception as e:
		bot.edit_message_text(mensaje_edit, index, callback.message.message_id, parse_mode=ParseMode.MARKDOWN)
		
	jugador_pregunton = game.playerlist[pregunta.uid]
	game.history.append("{}: {}".format(jugador_pregunton.name, pregunta_respuesta))
	game.board.state.preguntas_restantes -= 1
	bot.send_message(game.cid, "{}: {}".format(jugador_pregunton.name, pregunta_respuesta), ParseMode.MARKDOWN)

	save(bot, game.cid)
	
	# Si se acaban las pregutnas	
	if game.board.state.preguntas_restantes == 0 or not game.board.state.correcto:
		resolve(bot, game, job_queue)
	else:
		bot.send_message(game.cid, "Quedan *{}* preguntas!".format(game.board.state.preguntas_restantes), parse_mode=ParseMode.MARKDOWN)

	'''except Exception as e:
		bot.send_message(ADMIN[0], 'No se ejecuto el comando debido a: '+str(e))
		bot.send_message(ADMIN[0], callback.data)
	'''

def remove_jobs(job_queue, game):
	if job_queue is not None:
		for job in job_queue.get_jobs_by_name(game.cid):
			job.schedule_removal()

def resolve(bot, game, job_queue):
	# If doing resolve then eliminate job from job_queue if still there
	remove_jobs(job_queue, game)
	if not game.board.state.correcto:
		# Se inicia votacion preguntando a los hombre lobo
		bot.send_message(game.cid, "La palabra magica ha sido encontrada! *Era {}*".format(game.board.magic_word), parse_mode=ParseMode.MARKDOWN)
		iniciar_votacion(bot, game, "lobos")
	else:
		# Se inicia votacion para buscar hombres lobos
		bot.send_message(game.cid, "La palabra magica *NO* ha sido encontrada! *Era {}*".format(game.board.magic_word), parse_mode=ParseMode.MARKDOWN)			
		iniciar_votacion(bot, game, "aldeanos")

	# Si se pasa el argumento, y ha sido con tiempo inicialmente.
	if hasattr(game, 'using_timer') and game.using_timer:
		msg = "‼‼Tienen 2 minutos para decidir sus votos.‼‼"
		bot.send_message(game.cid, msg, parse_mode=ParseMode.MARKDOWN)
		contexto = [game, job_queue]
		job_queue.run_once(resolve_votacion, 120, context=contexto, name=game.cid)


def iniciar_votacion(bot, game, tipo_votacion):
	game.board.state.fase_actual = "votacion_desenmascarar"
	game.dateinitvote = datetime.datetime.now()
	game.board.state.last_votes = {}
	save(bot, game.cid)
	game.board.print_board(bot, game)	

	if(tipo_votacion == "lobos"):
		# Cada lobo vota en busca de la vidente
		call_other_players = ""
		lobos_ids = []
		for lobo in game.get_badguys():
			call_other_players += "{} ".format(player_call(lobo))
			lobos_ids.append(lobo.uid)
			opciones_botones = { player.uid : player.name  for player in game.player_sequence if player.uid not in lobos_ids }
			simple_choose_buttons(bot, game.cid, lobo.uid, lobo.uid, "choosevidenteWW", "¿Quien crees que es la vidente?", opciones_botones, False, 2)		
		if not game.board.state.aprendiz_vidente:
			msg = "Hombre/s lobo/s {} elijan a alguien que crean que sea la vidente, si la descubren ganan ustedes, pueden votar a diferentes personas!".format(call_other_players)
		else:
			msg = "Hombre/s lobo/s {} elijan a alguien que crean que sea la aprendiz. *El mayor no es*. Si la descubren ganan ustedes, pueden votar a diferentes personas!".format(call_other_players)

		bot.send_message(game.cid, msg, parse_mode=ParseMode.MARKDOWN)
	else:
		# Votan los aldeanos a los lobos
		msg = """Todos voten al mismo tiempo quien creen que es hombre lobo, si descubren a uno ganan la partida!

Los empates en votación juegan a favor de los aldeanos."""
		bot.send_message(game.cid, msg)
		for aldeano in game.player_sequence:
			opciones_botones = { player.uid : player.name  for player in game.player_sequence if player.uid != aldeano.uid }
			aldeano_uid = ADMIN[0] if game.is_debugging else aldeano.uid
			simple_choose_buttons(bot, game.cid, aldeano_uid, aldeano_uid, "chooseloboWW", "¿Quien crees que es lobo?", opciones_botones, False, 2)

def resolve_votacion(context: CallbackContext):	
	job = context.job
	bot = context.bot
	game = job.context[0]
	job_queue = job.context[1]
	if game.board.state.fase_actual == "Terminado":
		return
	if not game.board.state.correcto:
		# Lobos
		resolve_lobos(bot, game, job_queue)
	else:
		# Aldeanos
		resolve_aldeanos(bot, game, job_queue)

def callback_choose_vidente(update: Update, context: CallbackContext):
	bot = context.bot
	job_queue = context.job_queue
	log.info('callback_choose_vidente called')
	callback = update.callback_query
	try:
		regex = re.search("(-[0-9]*)\*choosevidenteWW\*(.*)\*([0-9]*)", callback.data)
		cid, opcion, uid = int(regex.group(1)), regex.group(2), int(regex.group(3))

		game = get_game(cid)
		jugador_elegido = game.playerlist[int(opcion)]

		valid_callback = game.validate_call_choose_vidente(uid)
		if not valid_callback:
			mensaje_edit = "No puedes o no es el momento para usar esta botonera"
			bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)
			return

		mensaje_edit = "Has elegido al jugador: {0}".format(jugador_elegido.name)
		try:
			bot.edit_message_text(mensaje_edit, cid, callback.message.message_id)
		except Exception as e:
			bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)
		
		game.board.state.last_votes[uid] = jugador_elegido		
		save(bot, game.cid)
		# Si ya han votado todos los lobos voy a la resolucion de lobos
		if len(game.get_badguys()) == len(game.board.state.last_votes):
			resolve_lobos(bot, game, job_queue)

	except Exception as e:
		bot.send_message(ADMIN[0], 'No se ejecuto el comando debido a: '+str(e))
		bot.send_message(ADMIN[0], callback.data)

def callback_choose_lobo(update: Update, context: CallbackContext):
	bot = context.bot
	job_queue = context.job_queue
	log.info('callback_choose_lobo called')
	callback = update.callback_query
	try:
		regex = re.search(r"(-[0-9]*)\*chooseloboWW\*(.*)\*([0-9]*)", callback.data)
		cid, opcion, uid = int(regex.group(1)), regex.group(2), int(regex.group(3))

		game = get_game(cid)
		
		valid_callback = game.validate_call_choose_lobo(uid)

		if not valid_callback:
			mensaje_edit = "No puedes o no es el momento para usar esta botonera"
			bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)
			return

		jugador_elegido = game.playerlist[int(opcion)]
		mensaje_edit = "Has elegido al jugador: {0}".format(jugador_elegido.name)
		try:
			bot.edit_message_text(mensaje_edit, cid, callback.message.message_id)
		except Exception as e:
			bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)
		
		game.board.state.last_votes[uid] = jugador_elegido
		save(bot, game.cid)

		aldeano = game.playerlist[uid]

		bot.send_message(game.cid, "*{}* ha votado".format(aldeano.name), parse_mode=ParseMode.MARKDOWN)

		# Si ya han votado todos los jugadores voy a la resolucion de aldeanos		
		if len(game.player_sequence) == len(game.board.state.last_votes):
			resolve_aldeanos(bot, game, job_queue)
		else:
			aldeano = game.playerlist[uid]
			opciones_botones = { player.uid : player.name  for player in game.player_sequence if player.uid != aldeano.uid }
			simple_choose_buttons(bot, game.cid, aldeano.uid, 
									aldeano.uid, "chooseloboWW", "*Por si te Arrepientes*\n¿Quien crees que es lobo?", 
									opciones_botones, False, 2)
	except Exception as e:
		bot.send_message(ADMIN[0], 'No se ejecuto el comando debido a: '+str(e))
		bot.send_message(ADMIN[0], callback.data)

def resolve_lobos(bot, game, job_queue):
	# Busco en los votos de los lobos, si alguno encontró a la vidente
	msg_not_found = "Ganan los aldeanos porque los lobos no encontraron a la vidente!"
	msg = ""
	found = False
	
	for uid, player in game.board.state.last_votes.items():
		finder = game.playerlist[uid]
		msg += "{} salta contra {} y lo despedaza!\n".format(player_call(finder), player_call(player))
		if (player.is_vidente() and not game.board.state.aprendiz_vidente) or (player.is_aprendiz() and game.board.state.aprendiz_vidente):
			found = True
			msg += "Ganan los lobos porque {} han encontrado a la {} {}!".format(player_call(finder), player.rol, player_call(player))
	if not found:
		msg += msg_not_found
	bot.send_message(game.cid, msg, parse_mode=ParseMode.MARKDOWN)
	end_game(bot, game, job_queue)

def resolve_aldeanos(bot, game, job_queue):
	# Busco en los votos de los lobos, si alguno encontró a la vidente
	msg = ""
	count_votes = { player.uid : 0  for player in game.player_sequence }
	# Cuento los votos
	for uid, player in game.board.state.last_votes.items():
		finder = game.playerlist[uid]
		msg += "{} apunta con el dedo a {}!\n\n".format(player_call(finder), player_call(player))
		count_votes[player.uid] += 1
	# Obtengo una lista de los mas votados
	maxValue = max(count_votes.values())  #<-- max of values
	aldeanos_mas_votados = [key for key in count_votes if count_votes[key]==maxValue]
	# Si todos los jugadores tienen 1 voto, los aldeanos pierden.
	if len(game.playerlist) == len(aldeanos_mas_votados):
		msg += "*Ganan los hombre lobo* ya que los aldeanos no se decidieron! (1 voto por jugador)"
	elif any(  game.playerlist[aldeano].rol in ("Hombre Lobo", "Secuaz") for aldeano in aldeanos_mas_votados):
		# Si alguno de los mas votados es Hombre Lobo o Secuaz, pierden los hombres lobo.
		msg += "*Ganan los aldeanos* porque han encontrado a un lobo o su secuaz!"
	else:
		msg += "*Ganan los hombre lobo* porque los aldeanos fallaron en encontrados!"

	bot.send_message(game.cid, msg, parse_mode=ParseMode.MARKDOWN)
	end_game(bot, game, job_queue)

def end_game(bot, game, job_queue):
	# Imprimo los jugadores y sus roles
	game.board.state.fase_actual = "Terminado"
	msn = "*Juego finalizado*"
	bot.send_message(game.cid, msn, ParseMode.MARKDOWN)
	remove_jobs(job_queue, game)
	save(bot, game.cid)
	bot.send_message(game.cid, game.print_roles(), parse_mode=ParseMode.MARKDOWN)
	bot.send_message(game.cid, "Para comenzar un nuevo juego borrame con /delete", parse_mode=ParseMode.MARKDOWN)
	continue_playing(bot, game)

def continue_playing(bot, game):
	opciones_botones = { "Nuevo" : "Nuevo Partido con nuevos jugadores", "Mismo Diccionario" : "Mismos jugadores, mismo Diccionario", "Otro Diccionario" : "Mismos jugadores, diferente diccionario"}
	simple_choose_buttons(bot, game.cid, 1, game.cid, "chooseendWW", "¿Quieres continuar jugando?", opciones_botones, False, 1)

def callback_finish_game_buttons(update: Update, context: CallbackContext):
	bot = context.bot
	callback = update.callback_query
	try:		
		log.info('callback_finish_game_buttons called: %s' % callback.data)	
		regex = re.search("(-[0-9]*)\*chooseendWW\*(.*)\*([0-9]*)", callback.data)
		cid, strcid, opcion, uid, struid = int(regex.group(1)), regex.group(1), regex.group(2), int(regex.group(3)), regex.group(3)
		mensaje_edit = "Has elegido: {0}".format(opcion)
		try:
			bot.edit_message_text(mensaje_edit, cid, callback.message.message_id)
		except Exception as e:
			bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)				
		
		game = get_game(cid)
		
		# Obtengo el diccionario actual, primero casos no tendre el config y pondre el community
		try:
			dicc = game.configs.get('diccionario','facil')
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
			game.configs['diccionario'] = dicc
			night_phase(bot, game)
			return
		elif opcion == "Otro Diccionario":
			init_game(bot, game)
			
	except Exception as e:
		bot.send_message(ADMIN[0], 'No se ejecuto el comando debido a: '+str(e))
		bot.send_message(ADMIN[0], callback.data)	

