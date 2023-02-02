#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Eduardo Peluffo"

import json
import logging as log
import random
import re
from random import randrange, choice
from time import sleep
from uuid import uuid4

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update, \
	InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import (InlineQueryHandler, Updater, CommandHandler, \
	CallbackQueryHandler, MessageHandler, Filters, CallbackContext)
from telegram.utils.helpers import mention_html, escape_markdown

import Commands
from Utils import get_game
import traceback
import sys

# Importo los controladores de todos los juegos que vaya agregando
import JustOne.Controller as JustOneController
import SayAnything.Controller as SayAnythingController
import Arcana.Controller as ArcanaController
import Wavelength.Controller as WavelengthController
import Decrypt.Controller as DecryptController
import Werewords.Controller as WerewordsController
import Deception.Controller as DeceptionController
import Unanimo.Controller as UnanimoController

# Importo los comandos de los juegos que vaya agregando
import JustOne.Commands as JustoneCommands
import LostExpedition.Commands as LostExpeditionCommands
import SayAnything.Commands as SayAnythingCommands
import Arcana.Commands as ArcanaCommands
import Wavelength.Commands as WavelengthCommands
import Decrypt.Commands as DecryptCommands
import Werewords.Commands as WerewordsCommands
import Deception.Commands as DeceptionCommands
import Unanimo.Commands as UnanimoCommands

from Constants.Cards import playerSets, actions
from Constants.Config import TOKEN, STATS, ADMIN
from Boardgamebox.Game import Game
from Boardgamebox.Player import Player
from Boardgamebox.Board import Board


import GamesController
import datetime
import pytz

import os
import psycopg2
import urllib.parse

# Enable logging

log.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=log.INFO)


logger = log.getLogger(__name__)

#DB Connection I made a Haroku Postgres database first
urllib.parse.uses_netloc.append("postgres")
url = urllib.parse.urlparse(os.environ["DATABASE_URL"])

# conn = psycopg2.connect(
#     database=url.path[1:],
#     user=url.username,
#     password=url.password,
#     host=url.hostname,
#     port=url.port
# )
'''
cur = conn.cursor()
query = "SELECT ...."
cur.execute(query)
'''

debugging = False

def player_call(player):
	return "[{0}](tg://user?id={1})".format(player.name, player.uid)

def init_game(bot, game):
	log.info('Game Init called')
	player_number = len(game.playerlist)
	game.board = Board(player_number, game)
	bot.send_message(game.cid, "Juego iniciado")
	
	if game.tipo == "LostExpedition":
		game.create_board()
		init_lost_expedition(bot, game, player_number)
	elif game.tipo == "JustOne":
		JustOneController.init_game(bot, game)
	elif game.tipo == "SayAnything":
		game.create_board()
		SayAnythingController.init_game(bot, game)
	elif game.tipo == "Arcana":
		game.create_board()
		ArcanaController.init_game(bot, game)
	elif game.tipo == "Wavelength":
		game.create_board()
		WavelengthController.init_game(bot, game)
	elif game.tipo == "Decrypt":
		game.create_board()
		DecryptController.init_game(bot, game)	
	elif game.tipo == "Werewords":
		game.create_board()
		WerewordsController.init_game(bot, game)
	elif game.tipo == "Deception":
		game.create_board()
		DeceptionController.init_game(bot, game)
	elif game.tipo == "Unanimo":
		game.create_board()
		UnanimoController.init_game(bot, game)


def init_lost_expedition(bot, game, player_number):
	log.info('Game init_lost_expedition called')	
	
	if player_number == 1:		
		bot.send_message(game.cid, "Vamos a llegar al dorado. Es un hermoso /dia!")
		# Aca deberia preguntar dificultad y modulos a usar.
		# Eso setearia la vida inicial y los personajes que tendria.
	else:
		# Se mezcla el orden de los jugadores.
		game.shuffle_player_sequence()
		# TODO Se deberia decir quien es el lider actual 
		bot.send_message(game.cid, "Vamos a llegar al dorado. Es un hermoso /dia!")
 
def increment_player_counter(game):
    log.info('increment_player_counter called')
    if game.board.state.player_counter < len(game.player_sequence) - 1:
        game.board.state.player_counter += 1
    else:
        game.board.state.player_counter = 0

def callback_announce(update: Update, context: CallbackContext):
	bot = context.bot	
	callback = update.callback_query
	log.info('callback_announce called: %s' % callback.data)
	try:		
		#log.info('callback_finish_game_buttons called: %s' % callback.data)	
		regex = re.search(r"(-?[0-9]*)\*announce\*(.*)\*(-?[0-9]*)", callback.data)
		cid, opcion, uid = int(regex.group(1)), regex.group(2), int(regex.group(3))
		
		if (opcion == "Cancel"):
			mensaje_edit = "Has cancelado el anuncio."
			bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)
			return
		
		
		mensaje_edit = "Has elegido anunciar en partidos de: {0}".format(opcion)
		
		try:
			bot.edit_message_text(mensaje_edit, cid, callback.message.message_id)
		except Exception as e:
			bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)				
		

		games = getGamesByTipo(opcion)
		
		
		
		mensaje = '‼️Anuncio cambios en {0}‼️\n\n{1}'.format(opcion, GamesController.announce_text)
		
		players = {}
		# Pongo a todos los jugadores en partidos de tal tipo
		for game in games.values():
			players.update(game.playerlist)
			
		for uid in players.keys():
			try:
				bot.send_message(uid, mensaje, ParseMode.MARKDOWN)
			except Exception as e:
				log.info(e)
	except Exception as e:
		bot.send_message(ADMIN[0], 'No se ejecuto el comando debido a: '+str(e))
		bot.send_message(ADMIN[0], callback.data)

def getGamesByTipo(opcion):
	games = None
	conn = psycopg2.connect(
		database=url.path[1:],
		user=url.username,
		password=url.password,
		host=url.hostname,
		port=url.port
	)
	cursor = conn.cursor()			
	log.info("Executing in DB")
	if opcion != "Todos":
		query = "select * from games g where g.tipojuego = '{0}'".format(opcion)
	else:
		query = "select * from games g"
	
	cursor.execute(query)
	if cursor.rowcount > 0:
		# Si encuentro juegos los busco a todos y los cargo en memoria
		for table in cursor.fetchall():
			if table[0] not in GamesController.games.keys():
				get_game(table[0])
		# En el futuro hacer que pueda hacer anuncios globales a todos los juegos ?
		games_restriction = [opcion]
		#bot.send_message(uid, "Obtuvo esta cantidad de juegos: {0}".format(len(GamesController.games)))
		# Luego aplico
		if opcion != "Todos":
			games = {key:val for key, val in GamesController.games.items() if val.tipo in games_restriction}
		else:
			games = GamesController.games
		conn.close()
	return games

def error(update, context):
    # add all the dev user_ids in this list. You can also add ids of channels or groups.
    devs = [ADMIN[0]]
    # we want to notify the user of this problem. This will always work, but not notify users if the update is an
	# callback or inline query, or a poll update. In case you want this, keep in mind that sending the message 
    # could fail
    '''
	if update.effective_message:
        text = "Hey. I'm sorry to inform you that an error happened while I tried to handle your update. " \
               "My developer(s) will be notified."
        update.effective_message.reply_text(text)
	'''
    # This traceback is created with accessing the traceback object from the sys.exc_info, which is returned as the
    # third value of the returned tuple. Then we use the traceback.format_tb to get the traceback as a string, which
    # for a weird reason separates the line breaks in a list, but keeps the linebreaks itself. So just joining an
    # empty string works fine.
    trace = "".join(traceback.format_tb(sys.exc_info()[2]))
    # lets try to get as much information from the telegram update as possible
    payload = ""
    # normally, we always have an user. If not, its either a channel or a poll update.
    if update.effective_user:
        payload += f' with the user {mention_html(update.effective_user.id, update.effective_user.first_name)}'
    # there are more situations when you don't get a chat
    if update.effective_chat:
        payload += f' within the chat <i>{update.effective_chat.title}</i>'
        if update.effective_chat.username:
            payload += f' (@{update.effective_chat.username})'
    # but only one where you have an empty payload by now: A poll (buuuh)
    if update.poll:
        payload += f' with the poll id {update.poll.id}.'
    # lets put this in a "well" formatted text
    text = f"Hey.\n The error <code>{context.error}</code> happened{payload}. The full traceback:\n\n<code>{trace}" \
           f"</code>"
    # and send it to the dev(s)
    for dev_id in devs:
        context.bot.send_message(dev_id, text, parse_mode=ParseMode.HTML)
    # we raise the error again, so the logger module catches it. If you don't use the logger module, use it.
    logger.warning('Update "%s" caused error "%s"', update, context.error)
        
# Metodo para recuperarse despues de un error de time out	
def recover(bot, update, game, uid):
	if game.tipo == "LostExpedition":
		recover_lost_expedition(bot, update, game, uid)
		
def recover_lost_expedition(bot, update, game, uid):
	# Si el juego no esta empezado, o no esta en ninguna fase. No hago nada.
	if game.board != None:		
		if game.board.state.fase_actual != None:
			if game.board.state.fase_actual == "resolve":
				# Si estaba en resolve quiere decir que hay que hacer el resolve.
				LostExpeditionCommands.resolve(bot, game.cid, uid, game, game.playerlist[uid])
			elif game.board.state.fase_actual == "execute_actions":
				Commands.command_continue(bot, [None, game.cid, uid])

def unknown(update: Update, context: CallbackContext):
	bot = context.bot
	bot.send_message(chat_id=update.message.chat_id, text="No conozco ese comando")

def add_group(update: Update, context: CallbackContext):
	cid = update.message.chat.id
	for member in update.message.new_chat_members:
		#ot.send_message(ADMIN[0], text="{username} {id} add group {groupname}".format(username=member.first_name, id=member.id, groupname = groupname, cid=cid))
		add_member_group(cid, member.id)
		add_user(member.id, member.first_name)

def add_member_group(cid, uid):
	try:
		#Check if game is in DB first
		conn = psycopg2.connect(
			database=url.path[1:],
			user=url.username,
			password=url.password,
			host=url.hostname,
			port=url.port
		)
		cur = conn.cursor()			
		#log.info("Searching Game in DB")
		query = "select * from users_group where group_id = %s and user_id = %s;"
		cur.execute(query, [cid, uid])
		#dbdata = cur.fetchone()
		if cur.rowcount == 0:
			#log.info(gamejson)
			query = "INSERT INTO users_group(group_id, user_id, alert_me) VALUES (%s, %s, %s) RETURNING user_id;"
			#query = "INSERT INTO games(id , groupName  , data) VALUES (%s, %s, %s) RETURNING data;"
			cur.execute(query, (cid, uid, True))
			#log.info(cur.fetchone()[0])
			conn.commit()
			conn.close()
	except Exception as e:
		log.info('No se grabo debido al siguiente error: '+str(e))
		conn.rollback()
		conn.close()

def add_user(uid, first_name):
	try:
		#Check if game is in DB first
		conn = psycopg2.connect(
			database=url.path[1:],
			user=url.username,
			password=url.password,
			host=url.hostname,
			port=url.port
		)
		cur = conn.cursor()			
		#log.info("Searching Game in DB")
		query = "select * from users where id = %s;"
		cur.execute(query, [uid])
		#dbdata = cur.fetchone()
		if cur.rowcount == 0:
			#log.info(gamejson)
			query = "INSERT INTO users(id, name) VALUES (%s, %s) RETURNING name;"
			#query = "INSERT INTO games(id , groupName  , data) VALUES (%s, %s, %s) RETURNING data;"
			cur.execute(query, (uid, first_name))
			#log.info(cur.fetchone()[0])
			conn.commit()
			conn.close()
	except Exception as e:
		log.info('No se grabo debido al siguiente error: '+str(e))
		conn.rollback()
		conn.close()

def remove_group(update: Update, context: CallbackContext):
	cid = update.message.chat.id
	#bot.send_message(ADMIN[0], "Entro en remove member {}".format(groupname))
	member = update.message.left_chat_member	
	bot = context.bot
	# Cuando un miembro se va lo remuevo de la BD
	remove_member_group(cid, member.id)
	uid = member.id
	# Me fijo si hay partida en ese grupo y si el miembro pertenece a la partida
	game = get_game(cid)
	if game:
		if uid in game.playerlist and hasattr(game, 'player_leaving'):
			resultado = game.player_leaving(game.playerlist[uid])
			if resultado:
				bot.send_message(cid, text=resultado)


	#for members in update.message.left_chat_member:
        #	bot.send_message(ADMIN[0], text="{username} {id} add group".format(username=members.username, id=member.id))
	
def remove_member_group(cid, uid):
	# Elimino al usuario al usuario en la tabla de usuario grupo
	try:
		#Check if game is in DB first
		conn = psycopg2.connect(
			database=url.path[1:],
			user=url.username,
			password=url.password,
			host=url.hostname,
			port=url.port
		)
		cur = conn.cursor()			
		#log.info("Searching Game in DB")
		query = "select * from users_group where group_id = %s and user_id = %s;"
		cur.execute(query, [cid, uid])
		#dbdata = cur.fetchone()
		if cur.rowcount > 0:			
			#log.info(gamejson)
			query = "DELETE from users_group where group_id = %s and user_id = %s;"
			cur.execute(query, (cid, uid))
			#log.info(cur.fetchone()[0])
			conn.commit()
			conn.close()	
	except Exception as e:
		log.info('No se elimino de la tabla de usarios debido a: '+str(e))
		conn.rollback()
		conn.close()



def put(update: Update, context: CallbackContext):
	args = context.args
	user_data = context.user_data
	"""Usage: /put value"""
	# Generate ID and seperate value from command
	key = 'pista'
	# Store value
	user_data[key] = args[0]

	update.message.reply_text(key)

def get(update: Update, context: CallbackContext):
	user_data = context.user_data
	# Load value
	try:
		value = user_data['pista']
		update.message.reply_text(value)
	except KeyError:
		update.message.reply_text('Not found')

def change_groupname(update: Update, context: CallbackContext):
	bot = context.bot
	logger.info(update)
	logger.info(context)
	cid = update.message.chat_id
	groupname = update.message.chat.title
	game = get_game(cid)
	if game:
		game.groupName = groupname
	
	bot.send_message(ADMIN[0], text="El group en {cid} ha cambiado de nombre a {groupname}".format(groupname=groupname, cid=cid))

def change_group_id(update: Update, context: CallbackContext):
	bot = context.bot
	logger.info(update)
	logger.info(context)
	cid = update.message.chat_id
	groupname = update.message.chat.title
	game = get_game(cid)
	if game:
		game.groupName = groupname
	
	bot.send_message(ADMIN[0], text=f"El group llamado {groupname} cambio al id {cid}")


def repeat_test(context: CallbackContext):
    context.bot.send_message(chat_id=387393551, text=context.job.context)

def get_TOKEN():	
	conn = psycopg2.connect(
		database=url.path[1:],
		user=url.username,
		password=url.password,
		host=url.hostname,
		port=url.port
	)
	cur = conn.cursor()
	query = "select * from config;"
	cur.execute(query)
	dbdata = cur.fetchone()
	token = dbdata[1]
	return token

def inlinequery(update: Update, context: CallbackContext):
	log.info(update)
	log.info(CallbackContext)	
	query = update.inline_query.query
	
	results = [
		InlineQueryResultArticle(
			id=uuid4(),
			title="⚖Exchange",
			input_message_content=InputTextMessageContent(
			'⚖Exchange')),
		InlineQueryResultArticle(
			id=uuid4(),
			title="⚒Workshop",
			input_message_content=InputTextMessageContent(
			'⚒Workshop',
			parse_mode=ParseMode.MARKDOWN)),
		InlineQueryResultArticle(
			id=uuid4(),
			title="📋Roster",
			input_message_content=InputTextMessageContent(
			'📋Roster')),
		InlineQueryResultArticle(
			id=uuid4(),
			title="🗃Misc",
			input_message_content=InputTextMessageContent(
			'🗃Misc')),
		InlineQueryResultArticle(
			id=uuid4(),
			title="⚒Crafting",
			input_message_content=InputTextMessageContent(
			'⚒Crafting')),		
		InlineQueryResultArticle(
			id=uuid4(),
			title="⚗️Alchemy",
			input_message_content=InputTextMessageContent(
			'⚗️Alchemy')),		
		InlineQueryResultArticle(
			id=uuid4(),
			title="🛎Auction",
			input_message_content=InputTextMessageContent(
			'🛎Auction',
			parse_mode=ParseMode.MARKDOWN)),
		InlineQueryResultArticle(
			id=uuid4(),
			title="🏚Shop",
			input_message_content=InputTextMessageContent(
			'🏚Shop',
			parse_mode=ParseMode.MARKDOWN)),
		InlineQueryResultArticle(
			id=uuid4(),
			title="🗺Quests",
			input_message_content=InputTextMessageContent(
			'🗺Quests',
			parse_mode=ParseMode.MARKDOWN)),
		InlineQueryResultArticle(
			id=uuid4(),
			title="▶️Fast fight",
			input_message_content=InputTextMessageContent(
			'▶️Fast fight',
			parse_mode=ParseMode.MARKDOWN))]
	update.inline_query.answer(results)

def main():
#def main():
	GamesController.init() #Call only once
	#initialize_testdata()

	#Init DB Create tables if they don't exist   
	log.info('Init DB in MultiGames Bot')
	conn = psycopg2.connect(
		database=url.path[1:],
		user=url.username,
		password=url.password,
		host=url.hostname,
		port=url.port
	)
	conn.autocommit = True
	cur = conn.cursor()
	cur.execute(open("DBCreate.sql", "r").read())
	log.info('DB Created/Updated')
	conn.autocommit = False
	'''
	log.info('Insertando')
	query = "INSERT INTO users(facebook_id, name , access_token , created) values ('2','3','4',1) RETURNING id;"
	log.info('Por ejecutar')
	cur.execute(query)       
	user_id = cur.fetchone()[0]        
	log.info(user_id)


	query = "SELECT ...."
	cur.execute(query)
	'''
	
	#NAME = "MultiGames"
	#PORT = os.environ.get('PORT')
	
	#PORT = int(os.environ.get('PORT', '8443'))		
	updater = Updater(os.environ.get('TOKEN_MULTIGAMES', None), use_context=True)

	'''
	updater2 = Updater('591941665:AAEDQgGEor55pvbwS9cEQ_OIRKdheO5RBY4')
	dp2 = updater.dispatcher
	dp2.add_handler(CommandHandler("start", Commands.command_start))
	updater2.start_polling()
	updater2.idle()
	'''
	# Get the dispatcher to register handlers
	dp = updater.dispatcher

	# on different commands - answer in Telegram
	dp.add_handler(CommandHandler("start", Commands.command_start))
	dp.add_handler(CommandHandler("help", Commands.command_help))
	dp.add_handler(CommandHandler("board", Commands.command_board))
	dp.add_handler(CommandHandler("rules", Commands.command_rules))
	dp.add_handler(CommandHandler("symbols", Commands.command_symbols))
	dp.add_handler(CommandHandler("players", Commands.command_jugadores))
	dp.add_handler(CommandHandler("newgame", Commands.command_newgame))
	dp.add_handler(CommandHandler("startgame", Commands.command_startgame))
	dp.add_handler(CommandHandler("delete", Commands.command_cancelgame))
	dp.add_handler(CommandHandler("join", Commands.command_join))
	dp.add_handler(CommandHandler("leave", Commands.command_leave))
	dp.add_handler(CommandHandler("history", Commands.command_showhistory))
	dp.add_handler(CommandHandler("ping", Commands.call_players_group))
	dp.add_handler(CommandHandler("call", Commands.command_call))
	dp.add_handler(CommandHandler("claim", Commands.command_claim))	
	dp.add_handler(CommandHandler("prueba", Commands.command_prueba))	
	# Comando para mandar mensajes al equipo
	dp.add_handler(CommandHandler("team", Commands.command_team))
	dp.add_handler(CommandHandler("kick", Commands.command_kick))
	dp.add_handler(CommandHandler("debug", Commands.command_toggle_debugging))
	
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosegameCHAT\*(.*)\*([0-9]*)", callback=Commands.callback_choose_game_chat))

	# Comando para hacer comandos sql desde el chat
	dp.add_handler(CommandHandler("comando", Commands.command_newgame_sql_command))
	dp.add_handler(CommandHandler("hojaayuda", Commands.command_hoja_ayuda))
	dp.add_handler(CommandHandler("reglas", Commands.command_reglas))	
	dp.add_handler(CommandHandler("save", Commands.save_comm))
	dp.add_handler(CommandHandler("load", Commands.load))
	dp.add_handler(CommandHandler("reload", Commands.reload))
	# Comando para preguntar los juegos que esperan mi accion.
	dp.add_handler(CommandHandler("myturn", Commands.command_myturn))
	dp.add_handler(CommandHandler("myturns", Commands.command_myturns))
	dp.add_handler(CommandHandler("pass", Commands.command_pass))
	dp.add_handler(CommandHandler("info", Commands.command_info))
	dp.add_handler(CommandHandler("admin", Commands.command_admin_games))
	
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*chooseGameInfo\*(.*)\*(-?[0-9]*)", callback=Commands.callback_info))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*chooseGameDelete\*(.*)\*(-?[0-9]*)", callback=Commands.callback_game_delete))
	
	# Configuracion de cualquier partida configurar para cada juego
	dp.add_handler(CommandHandler("config", Commands.command_configurar_partida))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosegame\*(.*)\*([0-9]*)", callback=Commands.callback_choose_game))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosemode\*(.*)\*([0-9]*)", callback=Commands.callback_choose_mode))
	dp.add_handler(CommandHandler("guess", Commands.command_guess))
	dp.add_handler(CommandHandler("pass", Commands.command_pass))	
	
	# Herramientas de ADMIN
	dp.add_handler(CommandHandler("ann", Commands.command_announce))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*announce\*(.*)\*(-?[0-9]*)", callback=callback_announce))
	dp.add_handler(CommandHandler("setconfig", Commands.command_set_config_data))
	dp.add_handler(CommandHandler("setstate", Commands.command_changestate))
	
	# Controller de Timers
	dp.add_handler(CommandHandler('timer', Commands.callback_timer))
	
	# Lost Expedition Commands
	dp.add_handler(CommandHandler("newgamelostexpedition", LostExpeditionCommands.command_newgame_lost_expedition))
	dp.add_handler(CommandHandler("drawcard", LostExpeditionCommands.command_drawcard))
	dp.add_handler(CommandHandler("showhand", LostExpeditionCommands.command_showhand))
	dp.add_handler(CommandHandler("losebullet", LostExpeditionCommands.command_losebullet))
	dp.add_handler(CommandHandler("gainbullet", LostExpeditionCommands.command_gainbullet))
	dp.add_handler(CommandHandler("losefood", LostExpeditionCommands.command_losefood))
	dp.add_handler(CommandHandler("gainfood", LostExpeditionCommands.command_gainfood))        
	dp.add_handler(CommandHandler("stats", LostExpeditionCommands.command_showstats))
	dp.add_handler(CommandHandler("campero", LostExpeditionCommands.command_vida_explorador_campero))
	dp.add_handler(CommandHandler("brujula", LostExpeditionCommands.command_vida_explorador_brujula))
	dp.add_handler(CommandHandler("hoja", LostExpeditionCommands.command_vida_explorador_hoja))
	dp.add_handler(CommandHandler("addrutefromhand", LostExpeditionCommands.command_add_exploration))
	dp.add_handler(CommandHandler("addrutefromdeck", LostExpeditionCommands.command_add_exploration_deck))
	dp.add_handler(CommandHandler("addrutefromhandfirst", LostExpeditionCommands.command_add_exploration_first))
	dp.add_handler(CommandHandler("moverutefirst", LostExpeditionCommands.command_add_exploration_deck_first))
	dp.add_handler(CommandHandler("swaprute", LostExpeditionCommands.command_swap_exploration))
	dp.add_handler(CommandHandler("removerute", LostExpeditionCommands.command_remove_exploration))
	dp.add_handler(CommandHandler("removelastrute", LostExpeditionCommands.command_remove_last_exploration))
	dp.add_handler(CommandHandler("showrute", LostExpeditionCommands.command_show_exploration))
	dp.add_handler(CommandHandler("sortrute", LostExpeditionCommands.command_sort_exploration_rute))
	dp.add_handler(CommandHandler("sorthand", LostExpeditionCommands.command_sort_hand))
	dp.add_handler(CommandHandler("showskills", LostExpeditionCommands.command_showskills))
	dp.add_handler(CommandHandler("gainprogreso", LostExpeditionCommands.command_increase_progreso))
	dp.add_handler(CommandHandler("removefirstrute", LostExpeditionCommands.command_resolve_exploration))
	dp.add_handler(CommandHandler("gainskill", LostExpeditionCommands.command_gain_skill))
	dp.add_handler(CommandHandler("useskill", LostExpeditionCommands.command_use_skill))
	dp.add_handler(CommandHandler("losecamp", LostExpeditionCommands.command_lose_camp))
	dp.add_handler(CommandHandler("losecompass", LostExpeditionCommands.command_lose_compass))
	dp.add_handler(CommandHandler("loseleaf", LostExpeditionCommands.command_lose_leaf))
	dp.add_handler(CommandHandler("loseexplorer", LostExpeditionCommands.command_lose_explorer))
	dp.add_handler(CommandHandler("resolve", LostExpeditionCommands.command_resolve_exploration2))
	dp.add_handler(CommandHandler("dia", LostExpeditionCommands.command_worflow))
	dp.add_handler(CommandHandler("noche", LostExpeditionCommands.command_worflow))
	# Lost Expedition Callbacks de botones
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*exe\*([^_]*)\*(.*)\*([0-9]*)", callback=LostExpeditionCommands.execute_command))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*opcioncomandos\*(.*)\*([0-9]*)", callback=LostExpeditionCommands.elegir_opcion_comando))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*opcionskill\*(.*)\*([0-9]*)", callback=LostExpeditionCommands.elegir_opcion_skill))	
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*commando\*([^_]*)\*swap\*([0-9]*)", callback=LostExpeditionCommands.callback_choose_swap))
			
	# Handlers de JustOne
	#dp.add_handler(CommandHandler("guess", JustoneCommands.command_guess))
	#dp.add_handler(CommandHandler("pass", JustoneCommands.command_pass))	
	dp.add_handler(CommandHandler("clue", JustoneCommands.command_clue))
	# Just One Callbacks de botones
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosedicc\*(.*)\*([0-9]*)", callback=JustOneController.callback_finish_config_justone))	
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*rechazar\*([0-9]*)", callback=JustOneController.callback_review_clues))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*finalizar\*(.*)\*([0-9]*)", callback=JustOneController.callback_review_clues_finalizado))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*reviewerconfirm\*(.*)\*([0-9]*)", callback=JustOneController.callback_reviewer_confirm))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosegameclue\*(.*)\*([0-9]*)", callback=JustoneCommands.callback_choose_game_clue))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*chooseend\*(.*)\*([0-9]*)", callback=JustOneController.callback_finish_game_buttons))
	
	# Handlers de SayAnything
	dp.add_handler(CommandHandler("resp", SayAnythingCommands.command_propose))
	dp.add_handler(CommandHandler("pick", SayAnythingCommands.command_pick))
	# Say Anything Callbacks de botones
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosediccSA\*(.*)\*([0-9]*)", callback=SayAnythingController.callback_finish_config))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosegamepropSA\*(.*)\*([0-9]*)", callback=SayAnythingCommands.callback_choose_game_prop))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*chooseendSA\*(.*)\*([0-9]*)", callback=SayAnythingController.callback_finish_game_buttons))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosegamepickSA\*(.*)\*([0-9]*)", callback=SayAnythingCommands.callback_choose_game_pick))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*voteRespuestaSA\*(.*)\*([0-9]*)", callback=SayAnythingController.callback_put_vote))
	
	# Handlers de Arcana
	# Arcana Callbacks de botones
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosediccAR\*(.*)\*([0-9]*)", callback=ArcanaController.callback_finish_config))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*txtArcanaAR\*(.*)\*([0-9]*)", callback=ArcanaController.callback_txt_arcana))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*chooseFateAR\*(.*)\*([0-9]*)", callback=ArcanaController.callback_choose_fate))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*chooseArcanaAR\*(.*)\*([0-9]*)", callback=ArcanaController.callback_choose_arcana))
	dp.add_handler(CommandHandler("remove", ArcanaCommands.command_remove))	
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*chooseendAR\*(.*)\*([0-9]*)", callback=ArcanaController.callback_finish_game_buttons))
	dp.add_handler(CommandHandler("discard", ArcanaCommands.command_discard))	
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*([A-Za-z]*)ArcanaAC\*(.*)\*(-?[0-9]*)", callback=ArcanaController.callback_choose_arcana_action))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*([A-Za-z]*)FateAC\*(.*)\*(-?[0-9]*)", callback=ArcanaController.callback_choose_fate_action))
	
	# Handlers de Wavelength
	dp.add_handler(CommandHandler("ref", WavelengthCommands.command_reference))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosegamerefWL\*(.*)\*([0-9]*)", callback=WavelengthCommands.callback_choose_game_prop))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*([A-Za-z]*)Wave\*(.*)\*(.*)", callback=WavelengthCommands.callback_Wave))
	dp.add_handler(CommandHandler("draw", WavelengthCommands.command_draw))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*chooseendWL\*(.*)\*([0-9]*)", callback=WavelengthController.callback_finish_game_buttons))
	
	
	# Handlers de Decrypt
	dp.add_handler(CommandHandler("code", DecryptCommands.command_code))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosegamerefDE\*(.*)\*([0-9]*)", callback=DecryptCommands.callback_choose_game_prop))
	#dp.add_handler(CallbackQueryHandler(pattern="(-?[0-9]*)\*([A-Za-z]*)Wave\*(.*)\*(.*)", callback=DecryptCommands.callback_Wave))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosediccDE\*(.*)\*([0-9]*)", callback=DecryptController.callback_finish_config_decrypt))
	
	dp.add_handler(CommandHandler("intercept", DecryptCommands.command_intercept))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosegameintDE\*(.*)\*([0-9]*)", callback=DecryptCommands.callback_choose_game_inter))
	
	dp.add_handler(CommandHandler("decrypt", DecryptCommands.command_decrypt))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosegamedecDE\*(.*)\*([0-9]*)", callback=DecryptCommands.callback_choose_game_dec))
	
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*chooseendDE\*(.*)\*([0-9]*)", callback=DecryptController.callback_finish_game_buttons))
	
	#dp.add_handler(CommandHandler("decrypt", DecryptCommands.command_decrypt))

	# Handlers de Werewords
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_moduloWW_(.*)", callback=WerewordsController.incluir_modulo))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosediccWW\*(.*)\*([0-9]*)", callback=WerewordsController.callback_finish_config_werewords))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*choosemagicwordWW\*(.*)\*(-?[0-9]*)", callback=WerewordsController.callback_choose_magic_word))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*choosepokeWW\*(.*)\*(-?[0-9]*)", callback=WerewordsController.callback_choose_poke))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*choosedopleWW\*(.*)\*(-?[0-9]*)", callback=WerewordsController.callback_choose_dople))
	dp.add_handler(CommandHandler("ask", WerewordsCommands.command_ask))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*askWW\*(.*)\*(-?[0-9]*)", callback=WerewordsController.callback_ask))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*choosevidenteWW\*(.*)\*(-?[0-9]*)", callback=WerewordsController.callback_choose_vidente))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*chooseloboWW\*(.*)\*(-?[0-9]*)", callback=WerewordsController.callback_choose_lobo))
	dp.add_handler(CommandHandler("toofar", WerewordsCommands.command_toofar))
	dp.add_handler(CommandHandler("soclose", WerewordsCommands.command_soclose))
	dp.add_handler(CommandHandler("undo", WerewordsCommands.command_undo))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*chooseendWW\*(.*)\*([0-9]*)", callback=WerewordsController.callback_finish_game_buttons))

	# Handlers de Deception
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_moduloDC_(.*)", callback=DeceptionController.incluir_modulo))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosediffDC\*(.*)\*([0-9]*)", callback=DeceptionController.callback_finish_config_werewords))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*choosemotivoDC\*(.*)\*(-?[0-9]*)", callback=DeceptionController.callback_choose_motivo))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*choosepistaDC\*(.*)\*(-?[0-9]*)", callback=DeceptionController.callback_choose_pista))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*choosecontinueDayDC\*(.*)\*(-?[0-9]*)", callback=DeceptionController.callback_choose_continue))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*chooseforensicDC\*(.*)\*(-?[0-9]*)", callback=DeceptionController.callback_choose_forensic))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*chooseforensicdetailDC\*(.*)\*(-?[0-9]*)", callback=DeceptionController.callback_choose_forensic_detail))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*chooseAccuseDE\*(.*)\*([0-9]*)", callback=DeceptionController.callback_accuse))
	#.add_handler(CommandHandler("undo", DeceptionCommands.command_undo))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*chooseendDC\*(.*)\*([0-9]*)", callback=DeceptionController.callback_finish_game_buttons))

	dp.add_handler(CommandHandler("newevidence", DeceptionCommands.command_evidence_collection))
	dp.add_handler(CommandHandler("accuse", DeceptionCommands.command_accuse))

	# Unanimo Comandos y Callbacks de botones
	dp.add_handler(CommandHandler("words", UnanimoCommands.command_words))
	dp.add_handler(CommandHandler("points", UnanimoCommands.command_points))
	
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosediccUnanimo\*(.*)\*([0-9]*)", callback=UnanimoController.callback_finish_config_unanimo))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosegamewords\*(.*)\*([0-9]*)", callback=UnanimoCommands.callback_choose_game_clue))
	# dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*rechazar\*([0-9]*)", callback=JustOneController.callback_review_clues))
	# dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*finalizar\*(.*)\*([0-9]*)", callback=JustOneController.callback_review_clues_finalizado))
	# dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*reviewerconfirm\*(.*)\*([0-9]*)", callback=JustOneController.callback_reviewer_confirm))
	# dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosegameclue\*(.*)\*([0-9]*)", callback=JustoneCommands.callback_choose_game_clue))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*chooseendunanimo\*(.*)\*([0-9]*)", callback=UnanimoController.callback_finish_game_buttons))

	# WEb Crapping commands
	dp.add_handler(CommandHandler("news", Commands.command_noticias))
	dp.add_handler(CommandHandler("imagen", Commands.command_image))
	# Handlers de D100
	dp.add_handler(CommandHandler("tirada", Commands.command_roll))
	
	dp.add_handler(CommandHandler('put', put, pass_args=True))	
	dp.add_handler(CommandHandler('get', get))	
	
	dp.add_handler(MessageHandler(Filters.command, unknown))
	
	# Handler cuando se una una persona al chat.
	#dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, add_group))
	
	# Handler cuando se va una persona del chat.
	#dp.add_handler(MessageHandler(Filters.status_update.left_chat_member, remove_group))
	
	# Handler cuando se cambia el nombre del chat 
	dp.add_handler(MessageHandler(Filters.status_update.new_chat_title, change_groupname))

	dp.add_handler(MessageHandler(Filters.status_update.migrate, change_group_id))

	# Inline query
	dp.add_handler(InlineQueryHandler(inlinequery))		
	
	job_que = updater.job_queue
	morning = datetime.time(13, 15, 0, 0, tzinfo=pytz.timezone("America/Argentina/Buenos_Aires"))


	job_que.run_daily(repeat_test, morning, context="Mensaje programado")
	job_que.start()

	# log all errors
	dp.add_error_handler(error)

	updater.bot.send_message(ADMIN[0], "Nueva version en linea")

	# Start the Bot (Usar si no es WebHook)
	updater.start_polling(timeout=30)
	
	# Configuracion para usar Web hook
	#pdater.start_webhook(listen="0.0.0.0", port=int(PORT), url_path=TOKEN)
	#pdater.bot.setWebhook("https://{}.herokuapp.com/{}".format(NAME, TOKEN))
	
	# Run the bot until the you presses Ctrl-C or the process receives SIGINT,
	# SIGTERM or SIGABRT. This should be used most of the time, since
	# start_polling() is non-blocking and will stop the bot gracefully.
	# Comentar cuando se usa de forma async
	updater.idle()




if __name__ == '__main__':
    main()
