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

from Unanimo.Boardgamebox.Player import Player
from Unanimo.Boardgamebox.Board import Board
from Unanimo.Boardgamebox.Game import Game

from Boardgamebox.Game import Game

from Utils import (next_player_after_active_player, remove_same_elements_dict,  increment_player_counter, get_config_data, player_call, simple_choose_buttons)

import GamesController
import datetime
from collections import Counter

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
		log.info('init_unanimo called')		
		game.shuffle_player_sequence()		
		# Seteo las palabras	
		call_dicc_buttons(bot, game)
	except Exception as e:
		bot.send_message(game.cid, 'No se ejecuto el comando debido a: '+str(e))

def call_dicc_buttons(bot, game):
	#log.info('call_dicc_buttons called')
	opciones_botones = { 
		"original" : "Español Original"
	}
	simple_choose_buttons(bot, game.cid, 1234, game.cid, "choosediccUnanimo", "¿Elija un diccionario para jugar?", opciones_botones)
		
def callback_finish_config_unanimo(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_finish_config_unanimo called')
	callback = update.callback_query
	try:
		regex = re.search(r"(-[0-9]*)\*choosediccUnanimo\*(.*)\*([0-9]*)", callback.data)
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
	log.info('finish_config_unanimo called')
	# Si vengo de un partido anterior agrego los descartes de la partida anterior.	
	if game.configs.get('discards', None):
		game.board.discards = game.configs.get('discards')
		del game.configs['discards']
	fill_cartas(game)
	game.board.state.progreso = 0
	start_round_unanimo(bot, game)

def fill_cartas(game):
	opcion = game.configs['diccionario']
	url_palabras_posibles = '/Unanimo/txt/spanish-{0}.txt'.format(opcion)	
	with open(url_palabras_posibles, 'r') as f:
		palabras_posibles = f.readlines()
		palabras_posibles_no_repetidas = list_menos_list(palabras_posibles, game.board.discards)
		# Si no hay palabra posible no repetidas para jugar mezclo todas las palabras posibles
		if len(palabras_posibles_no_repetidas) < 3:
		    # Quedo bien 
			game.board.discards = []
			palabras_posibles_no_repetidas = palabras_posibles
		
		random.shuffle(palabras_posibles_no_repetidas)		
		game.board.cartas = palabras_posibles_no_repetidas[0:3]
		game.board.cartas = [w.replace('\n', '') for w in game.board.cartas]

def start_round_unanimo(bot, game):
	log.info('start_round_unanimo called')
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
		#bot.send_message(cid, "Enviando mensaje a: %s" % game.playerlist[uid].name)
		mensaje = "Nueva palabra en el grupo {1}.\nLa palabra es: *{0}*, propone tus palabras representativas separadas por coma!".format(game.board.state.acciones_carta_actual, game.group_link_name())
		bot.send_message(uid, mensaje, ParseMode.MARKDOWN)
		mensaje = "Ejemplo: Si la palabra fuese (Fiesta)\n/words Cumpleaños, Torta, Decoracion, Musica, Rock, Infantil, Luces, Velas"
		bot.send_message(uid, mensaje, ParseMode.MARKDOWN)
	
def review_clues(bot, game):
	log.info('review_clues called')
	game.dateinitvote = None
	game.board.state.fase_actual = "Revisando Pistas"
	# reviewer_player = game.board.state.reviewer_player
	
	# bot.send_message(game.cid, "El revisor {0} esta viendo las pistas".format(reviewer_player.name), ParseMode.MARKDOWN)
		
	# reviewer_player = game.board.state.reviewer_player

	txt_words = "Las palabras escritas son:"
	for uid_pista, words in game.board.state.last_votes.items():
		player = game.playerlist[uid_pista]
		txt_words += f"\n*{player.name}*:\n{words}"
	bot.send_message(game.cid, txt_words, ParseMode.MARKDOWN)
	save(bot, game.cid)	
	players_points, contador_filtrado = count_points(game.board.state.last_votes)

	text_points = ""
	for uid, points in players_points.items():
		player = game.playerlist[uid]
		player.points += points
		text_points += f"El jugador *{player.name}* ha ganado {points} ahora tiene {player.points}\n"

	text_points_word = json.dumps(contador_filtrado, indent = 4)
	bot.send_message(game.cid, text_points_word, ParseMode.MARKDOWN)
	bot.send_message(game.cid, text_points, ParseMode.MARKDOWN)
	start_next_round(bot, game, True)

def count_points(last_votes):
	# lista para almacenar las palabras de todos los elementos
	lista_palabras = []

	# recorrer cada elemento del diccionario
	for uid, palabras in last_votes.items():
		# dividir las palabras en una lista
		lista_palabras += palabras.split(",")

	# contar las repeticiones de cada palabra
	contador = Counter(lista_palabras)

	# Filtrar palabras que se repiten más de una vez
	contador_filtrado = {k: v for k, v in contador.items() if v > 1}

	# Crear un nuevo diccionario para almacenar los valores de las palabras repetidas para cada uid
	dic_valores = {}
	for uid, votes in last_votes.items():
		# Obtener solo las palabras repetidas del valor del diccionario
		palabras_repetidas = [p for p in votes.split(',') if p in contador_filtrado]
		# sumar los valores para cada palabra
		suma_valores = sum(contador_filtrado[p] for p in palabras_repetidas)
		dic_valores[uid] = suma_valores

	# imprimir el resultado
	return dic_valores, contador_filtrado

def calculate_winner( game):
	best_player = max(game.player_sequence, key=lambda x: x.points)
	return best_player.name

def start_next_round(bot, game, failed = False):
	log.info('Verifing End_Game called')
	if (not game.board.cartas and game.modo != 'Extreme') or (game.modo == 'Extreme' and failed):
		# Si no quedan cartas se termina el juego y se muestra el puntaje.
		mensaje = f"Juego finalizado! El ganador es {calculate_winner(game)}"		
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
	start_round_unanimo(bot, game)

def continue_playing(bot, game):
	opciones_botones = { "Nuevo" : "Nuevo Partido con nuevos jugadores", "Mismo Diccionario" : "Mismo diccionario", "Otro Diccionario" : "Diferente diccionario"}
	msg = "¿Quieres continuar jugando? *Modo actual {}*. Si quieres cambiar de modo debes elegir nuevo partido".format(game.modo)
	simple_choose_buttons(bot, game.cid, 1, game.cid, "chooseendunanimo", msg, opciones_botones)
	
def callback_finish_game_buttons(update: Update, context: CallbackContext):
	bot = context.bot
	callback = update.callback_query
			
	#log.info('callback_finish_game_buttons called: %s' % callback.data)	
	regex = re.search(r"(-[0-9]*)\*chooseendunanimo\*(.*)\*([0-9]*)", callback.data)
	cid, opcion, uid = int(regex.group(1)), regex.group(2), int(regex.group(3))
	mensaje_edit = "Has elegido el diccionario: {0}".format(opcion)
	try:
		bot.edit_message_text(mensaje_edit, cid, callback.message.message_id)
	except Exception as e:
		bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)				
	game = get_game(cid)
	
	# Obtengo el diccionario actual, primero casos no tendre el config y pondre el community
	try:
		dicc = game.configs.get('diccionario','original')
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
	game.resetPlayerPoints()
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