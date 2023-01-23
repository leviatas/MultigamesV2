import json
import logging as log
import datetime
import os
import psycopg2
import urllib.parse
import sys
from time import sleep

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update, ForceReply, Update
from telegram.ext import (CallbackContext)

import MainController
import GamesController

from Boardgamebox.Board import Board
from Boardgamebox.Game import Game
from Boardgamebox.Player import Player
from Boardgamebox.State import State



import random
import re
# Objetos que uso de prueba estaran en el state

# Enable logging
log.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=log.INFO)
logger = log.getLogger(__name__)


def command_roll(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	from Utils import get_game, save
	
	if args:
		text_tirada = '¡Tu tirada de ' + ' '.join(args)
	else:
		text_tirada = '¡Tu tirada'
	
	cid = update.message.chat_id
	uid = update.message.from_user.id
	
	tirada = random.randint(1,101)	
	if tirada > 97:
		tirada2 = random.randint(1,101)
		text_tirada +=  ' es *%s!*' % (str(tirada+tirada2))
	elif tirada < 4:
		tirada2 = random.randint(1,101)
		text_tirada +=  ' es *%s!*' % (str(tirada-tirada2))
	elif tirada == 27:
		text_tirada +=  ' es *Épico*!' % (str(tirada+tirada2))		
	else:
		text_tirada +=  ' es *%s!*' % (str(tirada))
		
	bot.send_message(cid, "%s" % (text_tirada), ParseMode.MARKDOWN)
	
	# Si hay un juego creado guardo en el historial
	game = get_game(cid)
	if game and uid in game.playerlist:
		#bot.send_message(cid, "Grabo en base de datos", ParseMode.MARKDOWN)
		player = game.playerlist[uid]
		texthistory = "Jugador *%s* - %s" % (player.name, text_tirada)
		game.history.append("%s" % (texthistory))
