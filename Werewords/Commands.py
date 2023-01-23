import json
import logging as log
import datetime
#import ast
import jsonpickle
import os
import psycopg2
import urllib.parse

	
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update, Update
from telegram.ext import (CallbackContext)
from Werewords.Boardgamebox.Pregunta import Pregunta as Pregunta

from Utils import get_game, save, simple_choose_buttons
from Utils import player_call

import Werewords.Controller as WerewordsController
from Werewords.Boardgamebox.Board import Board
from Werewords.Boardgamebox.Game import Game
from Werewords.Boardgamebox.Player import Player
from Werewords.Boardgamebox.State import State
from Constants.Config import ADMIN
from collections import namedtuple
from datetime import datetime
from datetime import timedelta
# Enable logging

log.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=log.INFO)
logger = log.getLogger(__name__)

def command_ask(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args

	# Se crean botones y pone pregunta para el mayor.
	try:
		cid = update.message.chat_id
		uid = update.message.from_user.id
		mensaje_error = "Tienes que hacer una pregunta para responder"
		if len(args) > 0:
			# Si hizo una pregunta verifico si puede hacerla o termino el tiempo / cantidad de preguntas.
			game = get_game(cid)

			if uid not in game.playerlist:
				bot.send_message(cid, "Debes ser un jugador del partido para preguntar algo.")
				return

			if uid == game.board.state.mayor.uid:
				bot.send_message(cid, "Mayor vos no podes hacer preguntas!")
				return

			if game.board.state.fase_actual != "preguntar":
				bot.send_message(cid, "No es momento de preguntar!")
				return

			if game.board.state.preguntas_restantes > 0:				
				# Siempre estan estos botones
				opciones_botones = { "Si" : "Si", "No" : "No", "Tal Vez" : "Tal Vez"}
				if game.board.state.muy_cerca:
					opciones_botones["Muy Cerca"] = "Muy Cerca"
				if game.board.state.correcto:
					opciones_botones["Correcto"] = "Correcto"
				pregunta = ' '.join(args)
				
				index = len(game.board.state.preguntas_pendientes)				
				game.board.state.preguntas_pendientes.append(Pregunta(uid, pregunta, index + 1))
				pregunta = "{}: {}".format(player_call(game.get_mayor()), pregunta)

				#chat_data[uid] = pregunta
				simple_choose_buttons(bot, game.cid, index, game.cid, "askWW", pregunta, opciones_botones, False)
				save(bot, game.cid)
			else:
				mensaje_error = "Ya no hay preguntas restantes"
				bot.send_message(uid, mensaje_error)
		else:
			bot.send_message(uid, mensaje_error)
	except Exception as e:
		bot.send_message(uid, str(e))
		log.error("Unknown error: " + str(e))

def command_toofar(update: Update, context: CallbackContext):
	bot = context.bot
	# Se crean botones y pone pregunta para el mayor.
	try:
		cid = update.message.chat_id
		uid = update.message.from_user.id
		
		game = get_game(cid)

		if uid != game.board.state.mayor.uid:
			jugador_presiono = game.playerlist[uid]
			bot.send_message(cid, "*{}* tu *NO* puedes usar este comando!".format(jugador_presiono.name), parse_mode=ParseMode.MARKDOWN)
			return
		else:
			if game.board.state.muy_lejos:
				game.board.state.muy_lejos = False
				game.history.append("MUY LEJOS")
				bot.send_message(cid, "*MUY LEJOS*", parse_mode=ParseMode.MARKDOWN)
			else:
				bot.send_message(cid, "YA se ha usado el token de *MUY LEJOS*!", parse_mode=ParseMode.MARKDOWN)
	except Exception as e:
		bot.send_message(uid, str(e))
		log.error("Unknown error: " + str(e))

def command_soclose(update: Update, context: CallbackContext):
	bot = context.bot
	# Se crean botones y pone pregunta para el mayor.
	try:
		cid = update.message.chat_id
		uid = update.message.from_user.id
		
		game = get_game(cid)

		if uid != game.board.state.mayor.uid:
			jugador_presiono = game.playerlist[uid]
			bot.send_message(cid, "*{}* tu *NO* puedes usar este comando!".format(jugador_presiono.name), parse_mode=ParseMode.MARKDOWN)
			return
		else:
			if game.board.state.muy_cerca:
				game.board.state.muy_cerca = False
				game.history.append("MUY CERCA")
				bot.send_message(cid, "*MUY CERCA*", parse_mode=ParseMode.MARKDOWN)
			else:
				bot.send_message(cid, "YA se ha usado el token de *Muy CERCA*!", parse_mode=ParseMode.MARKDOWN)
	except Exception as e:
		bot.send_message(uid, str(e))
		log.error("Unknown error: " + str(e))

def command_call(context, game):
	try:
		bot = context.bot
		if game.board.state.fase_actual == "preguntar":
			# Se esta preguntando muestro todas las preguntas pendientes:
			hay_pendientes = any(pregunta.respuesta is None for pregunta in game.board.state.preguntas_pendientes)
			
			if hay_pendientes:
				msg = "{} tienes preguntas pendientes".format(player_call(game.get_mayor()))
				bot.send_message(game.cid, msg, parse_mode=ParseMode.MARKDOWN)				
				for idx, val in enumerate(game.board.state.preguntas_pendientes):
					if val.respuesta is None:					
						opciones_botones = { "Si" : "Si", "No" : "No", "Tal Vez" : "Tal Vez"}
						if game.board.state.muy_cerca:
							opciones_botones["Muy Cerca"] = "Muy Cerca"
						if game.board.state.correcto:
							opciones_botones["Correcto"] = "Correcto"						
						simple_choose_buttons(bot, game.cid, idx, game.cid, "askWW", val.pregunta, opciones_botones, False)
			else:
				msg = "No hay preguntas pendientes\nHagan preguntas: "
				for player in game.playerlist.values():
					if player.rol != "Mayor":
						msg += "{} ".format(player_call(player))
				bot.send_message(game.cid, msg, parse_mode=ParseMode.MARKDOWN)
		elif game.board.state.fase_actual == "votacion_desenmascarar":
			start = game.dateinitvote
			stop = datetime.now()          
			elapsed = stop - start
			if elapsed > timedelta(minutes=1):
				# Only remember to vote to players that are still in the game
				history_text = ""				
				# Si se encontro la palabra...
				if not game.board.state.correcto:
					lobos_ids = []
					for lobo in game.get_badguys():
						# If the player is not in last_votes send him reminder
						lobos_ids.append(lobo.uid)
						if lobo.uid not in game.board.state.last_votes:
							history_text += "Debes elegir a quien eliminar {}!\n".format(player_call(lobo))
							opciones_botones = { player.uid : player.name  for player in game.player_sequence if player.uid != lobo.uid }
							simple_choose_buttons(bot, game.cid, lobo.uid, lobo.uid, "choosevidenteWW", "¿Quien crees que es la vidente?", opciones_botones)
				
				else:
					for aldeano in game.player_sequence:
						# If the player is not in last_votes send him reminder
						if aldeano.uid not in game.board.state.last_votes:
							history_text += "Debes votar a quien eliminar {}!\n".format(player_call(aldeano))
							opciones_botones = { player.uid : player.name  for player in game.player_sequence if player.uid != aldeano.uid }
							simple_choose_buttons(bot, game.cid, aldeano.uid, aldeano.uid, "chooseloboWW", "¿Quien crees que es lobo?", opciones_botones)
					if history_text == "" :
						WerewordsController.resolve_aldeanos(bot, game, context.job_queue)
						return 
						
				if history_text == "" and not game.board.state.correcto:
					WerewordsController.resolve_lobos(bot, game, context.job_queue)
					return 		
					
				bot.send_message(game.cid, text=history_text, parse_mode=ParseMode.MARKDOWN)
			else:
				bot.send_message(game.cid, "Cinco minutos deben pasar para pedir que se vote!")
			
			

		
	except Exception as e:
		bot.send_message(game.cid, str(e))

def callback_timer(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	job_queue = context.job_queue
	
	cid = update.message.chat_id
	game = get_game(cid)

	if len(args) == 0:
		args = ["8","28"]

	bot.send_message(chat_id=cid, text='Comienzen a preguntar hay {} minutos y {} preguntas!'.format(args[0], args[1]))
	
	game = get_game(cid)

	game.using_timer = True

	game.board.state.preguntas_restantes = int(args[1])

	contexto = [job_queue, game.cid]
	
	# Paso los minutos a segundos y le resto los segundos del primer warning
	segundos_totales = (int(args[0])-1)*60

	job_queue.run_once(callback_alarm, segundos_totales, context=contexto, name=game.cid)

def callback_alarm(context: CallbackContext):
	job = context.job
	bot = context.bot
	cid = job.context[1]
	game = get_game(cid)

	# Si se ha terminado o comenzo la votacion
	if game.board.state.fase_actual in ["Terminado", "votacion_desenmascarar"]:
		return

	if not hasattr(game.board.state, 'warning'):
		game.board.state.warning = 60
	
	game.board.state.warning -= 30
	
	save(bot, game.cid)	
	# Si hay tiempo de warning re ejecuto con tiempo restante.
	job_queue = job.context[0]
	if game.board.state.warning >= 0:		
		contexto = [job_queue, game.cid]
		tiempo_restante = game.board.state.warning + 30
		bot.send_message(cid, '️‼‼*️️️Quedan {} segundos*‼‼'.format(tiempo_restante), parse_mode=ParseMode.MARKDOWN)
		# Se hace una alerta de que queda 1 minuto, y luego de 30 segundos ambos con internvalos de 30 segundos.
		job_queue.run_once(callback_alarm, 30, context=contexto, name=game.cid)
	else:
		bot.send_message(cid, text='‼‼*️️️El tiempo ha terminado*‼‼', parse_mode=ParseMode.MARKDOWN)
		WerewordsController.resolve(bot, game, job_queue)

def command_undo(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id

	game = get_game(cid)

	# Si esta creado el juego y esta iniciado.
	if game and game.board:
		preguntas = game.board.state.preguntas_pendientes
		msg = '‼‼*️️️No hay preguntas para hacer UNDO ahora*‼‼'
		if len(preguntas) > 0:
			ultima_pregunta_respondida = next((pregunta for pregunta in reversed(preguntas) if pregunta.respuesta is not None), None)
			if ultima_pregunta_respondida is not None:
				opcion = ultima_pregunta_respondida.respuesta
				# Vuelvo el flag a su forma anterior.
				if opcion == "MUY LEJOS":
					game.board.state.muy_lejos = True
				if opcion == "MUY CERCA":
					game.board.state.muy_cerca = True
				if opcion == "CORRECTO":
					game.board.state.correcto = True

				ultima_pregunta_respondida.respuesta = None
				bot.send_message(cid, '‼‼Se hizo undo de ultima pregunta: {}‼‼'.format(ultima_pregunta_respondida.pregunta), parse_mode=ParseMode.MARKDOWN)
				return
		return bot.send_message(cid, text=msg, parse_mode=ParseMode.MARKDOWN)
				
	else:
		bot.send_message(cid, text='‼‼*️️️No se puede hacer UNDO ahora*‼‼', parse_mode=ParseMode.MARKDOWN)



