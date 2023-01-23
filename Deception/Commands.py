import json
import logging as log
import datetime
#import ast
import jsonpickle
import os
import psycopg2
import urllib.parse

from random import randrange
	
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update, Update
from telegram.ext import (CallbackContext)

from Utils import get_game, save

from Deception.Boardgamebox.Pregunta import Pregunta as Pregunta
from Deception.Constants.Cards import FORENSIC_CARDS

import copy
import Deception.Controller as DeceptionController
from Deception.Boardgamebox.Board import Board
from Deception.Boardgamebox.Game import Game
from Deception.Boardgamebox.State import State
from Constants.Config import ADMIN
from collections import namedtuple
from datetime import datetime
from datetime import timedelta
# Enable logging

log.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=log.INFO)
logger = log.getLogger(__name__)

def command_evidence_collection(update: Update, context: CallbackContext):
	bot = context.bot
	try:
		cid = update.message.chat_id
		uid = update.message.from_user.id		
		game = get_game(cid)

		game.board.state.fase_actual = "evidence_collection"
		forense = game.board.state.forense
		'''
		if uid != forense.uid or forense.bullet_marker != 0:
			msg = "*No eres el forense o no es momento de recoletar nueva información!*"
			bot.send_message(cid, msg, parse_mode=ParseMode.MARKDOWN)
			return
		'''
		# Le doy una bala para poner
		forense.bullet_marker += 1
		# Le pido que elija una carta para reemplazar
		# Pongo la carta en state y se la muestro al forense. Que elija una carta para reemplazarla.
		scene_event_cards = game.board.state.scene_event_cards
		random_index = randrange(len(scene_event_cards))
		scene_desc = scene_event_cards.pop(random_index)

		game.board.state.new_scene_event_card.append({ scene_desc : copy.deepcopy(FORENSIC_CARDS["scene"][scene_desc]) })
		msg = "La nueva carta es:\n{}".format(game.board.get_forensic_cards_description(False, False, False))
		# Le muestro al forense la nueva carta
		DeceptionController.send_message(bot, game, forense, msg)

		DeceptionController.choose_forensic_card_menu(bot, game, False, True)
	except Exception as e:
		bot.send_message(uid, str(e))
		raise e

def command_accuse(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	uid = update.effective_user.id
	game = get_game(cid)
	DeceptionController.accuse(bot, game, uid)


def command_call(bot, game):
	try:
		DeceptionController.choose_forensic_card_menu(bot, game, game.board.state.check_has_bullet, game.board.state.only_scenes)		
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
		#DeceptionController.resolve(bot, game, job_queue)

def command_undo(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	#uid = update.effective_user.id

	game = get_game(cid)
	# Si esta creado el juego y esta iniciado.
	if game and game.board:		
		msg = '‼‼*️️️No se puede hacer UNDO ahora*‼‼'		
		return bot.send_message(cid, text=msg, parse_mode=ParseMode.MARKDOWN)				
	else:
		bot.send_message(cid, text='‼‼*️️️No se puede hacer UNDO ahora*‼‼', parse_mode=ParseMode.MARKDOWN)



