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

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, \
	InlineQueryResultArticle, InputTextMessageContent
from telegram.constants import ParseMode
from telegram.ext import (Application, InlineQueryHandler, CommandHandler, \
	CallbackQueryHandler, MessageHandler, filters, CallbackContext)
from telegram.helpers import mention_html, escape_markdown

import Commands
from Utils import get_game, command_status
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
import SecretoCodigo.Controller as SecretoCodigoController
import SpyFall.Controller as SpyFallController
import Insider.Controller as InsiderController
import BattlestarGalactica.Controller as BSGController

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
import SecretoCodigo.Commands as SecretoCodigoCommands
import SpyFall.Commands as SpyFallCommands
import Insider.Commands as InsiderCommands
import BattlestarGalactica.Commands as BSGCommands

from Constants.Cards import playerSets, actions
from Constants.Config import TOKEN, STATS, ADMIN
from Boardgamebox.Game import Game
from Boardgamebox.Player import Player
from Boardgamebox.Board import Board


import GamesController
import datetime
import pytz

import os
import psycopg
import urllib.parse

import asyncio
# Enable logging

log.basicConfig(
        format='%(asctime)s - Multigames - %(levelname)s - %(message)s',
        level=log.INFO)


logger = log.getLogger(__name__)

#DB Connection I made a Haroku Postgres database first
urllib.parse.uses_netloc.append("postgres")
url = urllib.parse.urlparse(os.environ["DATABASE_URL"])

# conn = psycopg.connect(
#     dbname=url.path[1:],
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

async def init_game(bot, game):
	log.info('Game Init called')
	player_number = len(game.playerlist)
	game.board = Board(player_number, game)
	await bot.send_message(game.cid, "Juego iniciado")
	
	if game.tipo == "LostExpedition":
		game.create_board()
		await init_lost_expedition(bot, game, player_number)
	elif game.tipo == "JustOne":
		await JustOneController.init_game(bot, game)
	elif game.tipo == "SayAnything":
		game.create_board()
		await SayAnythingController.init_game(bot, game)
	elif game.tipo == "Arcana":
		game.create_board()
		await ArcanaController.init_game(bot, game)
	elif game.tipo == "Wavelength":
		game.create_board()
		await WavelengthController.init_game(bot, game)
	elif game.tipo == "Decrypt":
		game.create_board()
		await DecryptController.init_game(bot, game)	
	elif game.tipo == "Werewords":
		game.create_board()
		await WerewordsController.init_game(bot, game)
	elif game.tipo == "Deception":
		game.create_board()
		await DeceptionController.init_game(bot, game)
	elif game.tipo == "Unanimo":
		game.create_board()
		await UnanimoController.init_game(bot, game)
	elif game.tipo == "SecretoCodigo":
		game.create_board()
		await SecretoCodigoController.init_game(bot, game)
	elif game.tipo == "SpyFall":
		game.create_board()
		await SpyFallController.init_game(bot, game)
	elif game.tipo == "Insider":
		game.create_board()
		await InsiderController.init_game(bot, game)
	elif game.tipo == "BattlestarGalactica":
		game.create_board()
		await BSGController.init_game(bot, game)


async def init_lost_expedition(bot, game, player_number):
	log.info('Game init_lost_expedition called')	
	
	if player_number == 1:		
		await bot.send_message(game.cid, "Vamos a llegar al dorado. Es un hermoso /dia!")
		# Aca deberia preguntar dificultad y modulos a usar.
		# Eso setearia la vida inicial y los personajes que tendria.
	else:
		# Se mezcla el orden de los jugadores.
		game.shuffle_player_sequence()
		# TODO Se deberia decir quien es el lider actual 
		await bot.send_message(game.cid, "Vamos a llegar al dorado. Es un hermoso /dia!")
 
def increment_player_counter(game):
    log.info('increment_player_counter called')
    if game.board.state.player_counter < len(game.player_sequence) - 1:
        game.board.state.player_counter += 1
    else:
        game.board.state.player_counter = 0

async def callback_announce(update: Update, context: CallbackContext):
	bot = context.bot	
	callback = update.callback_query
	log.info('callback_announce called: %s' % callback.data)
	try:		
		#log.info('callback_finish_game_buttons called: %s' % callback.data)	
		regex = re.search(r"(-?[0-9]*)\*announce\*(.*)\*(-?[0-9]*)", callback.data)
		cid, opcion, uid = int(regex.group(1)), regex.group(2), int(regex.group(3))
		
		if (opcion == "Cancel"):
			mensaje_edit = "Has cancelado el anuncio."
			await bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)
			return
		
		
		mensaje_edit = "Has elegido anunciar en partidos de: {0}".format(opcion)
		
		try:
			await bot.edit_message_text(mensaje_edit, cid, callback.message.message_id)
		except Exception as e:
			await bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)				
		

		games = getGamesByTipo(opcion)
		
		
		
		mensaje = '‼️Anuncio cambios en {0}‼️\n\n{1}'.format(opcion, GamesController.announce_text)
		
		players = {}
		# Pongo a todos los jugadores en partidos de tal tipo
		for game in games.values():
			players.update(game.playerlist)
			
		for uid in players.keys():
			try:
				await bot.send_message(uid, mensaje, ParseMode.MARKDOWN)
			except Exception as e:
				log.info(e)
	except Exception as e:
		await bot.send_message(ADMIN[0], 'No se ejecuto el comando debido a: '+str(e))
		await bot.send_message(ADMIN[0], callback.data)

def getGamesByTipo(opcion):
	games = None
	conn = psycopg.connect(
		dbname=url.path[1:],
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
		#await bot.send_message(uid, "Obtuvo esta cantidad de juegos: {0}".format(len(GamesController.games)))
		# Luego aplico
		if opcion != "Todos":
			games = {key:val for key, val in GamesController.games.items() if val.tipo in games_restriction}
		else:
			games = GamesController.games
		conn.close()
	return games

async def error(update, context):
	# add all the dev user_ids in this list. You can also add ids of channels or groups.
	devs = [ADMIN[0]]

	# We want to notify the user of this problem. This will always work for normal messages,
	# but may not for callback/inline/poll updates. Keep the old snippet commented for reference.
	'''
	if update.effective_message:
		text = "Hey. I'm sorry to inform you that an error happened while I tried to handle your update. " \
			   "My developer(s) will be notified."
		update.effective_message.reply_text(text)
	'''

	# Build traceback and payload
	trace = "".join(traceback.format_tb(sys.exc_info()[2]))
	payload = ""
	if update.effective_user:
		payload += f' with the user {mention_html(update.effective_user.id, update.effective_user.first_name)}'
	if update.effective_chat:
		payload += f' within the chat <i>{update.effective_chat.title}</i>'
		if update.effective_chat.username:
			payload += f' (@{update.effective_chat.username})'
	if update.poll:
		payload += f' with the poll id {update.poll.id}.'

	text = (
		f"Hey.\n The error <code>{context.error}</code> happened{payload}. The full traceback:\n\n<code>{trace}</code>"
	)

	# Send the error message to devs (best effort)
	for dev_id in devs:
		try:
			await context.bot.send_message(dev_id, text, parse_mode=ParseMode.HTML)
		except Exception:
			logger.exception("Failed to notify dev %s about error", dev_id)

	# Log the original error as well
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

async def unknown(update: Update, context: CallbackContext):
	bot = context.bot
	await bot.send_message(chat_id=update.message.chat_id, text="No conozco ese comando")

def add_group(update: Update, context: CallbackContext):
	cid = update.message.chat.id
	for member in update.message.new_chat_members:
		#ot.send_message(ADMIN[0], text="{username} {id} add group {groupname}".format(username=member.first_name, id=member.id, groupname = groupname, cid=cid))
		add_member_group(cid, member.id)
		add_user(member.id, member.first_name)

def add_member_group(cid, uid):
	try:
		#Check if game is in DB first
		conn = psycopg.connect(
			dbname=url.path[1:],
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
		conn = psycopg.connect(
			dbname=url.path[1:],
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

async def remove_group(update: Update, context: CallbackContext):
	cid = update.message.chat.id
	#await bot.send_message(ADMIN[0], "Entro en remove member {}".format(groupname))
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
				await bot.send_message(cid, text=resultado)


	#for members in update.message.left_chat_member:
        #	await bot.send_message(ADMIN[0], text="{username} {id} add group".format(username=members.username, id=member.id))
	
def remove_member_group(cid, uid):
	# Elimino al usuario al usuario en la tabla de usuario grupo
	try:
		#Check if game is in DB first
		conn = psycopg.connect(
			dbname=url.path[1:],
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

async def change_groupname(update: Update, context: CallbackContext):
	bot = context.bot
	logger.info(update)
	logger.info(context)
	cid = update.message.chat_id
	groupname = update.message.chat.title
	game = get_game(cid)
	if game:
		game.groupName = groupname
	
	await bot.send_message(ADMIN[0], text="El group en {cid} ha cambiado de nombre a {groupname}".format(groupname=groupname, cid=cid))

async def change_group_id(update: Update, context: CallbackContext):
	bot = context.bot
	logger.info(update)
	logger.info(context)
	cid = update.message.chat_id
	groupname = update.message.chat.title
	game = get_game(cid)
	if game:
		game.groupName = groupname
	
	await bot.send_message(ADMIN[0], text=f"El group llamado {groupname} cambio al id {cid}")


async def repeat_test(context: CallbackContext):
	# Send a fixed scheduled message (JobQueue no longer accepts a `context` kwarg)
	await context.bot.send_message(chat_id=387393551, text="Mensaje programado")

def get_TOKEN():	
	conn = psycopg.connect(
		dbname=url.path[1:],
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

async def inlinequery(update: Update, context: CallbackContext):
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
	await update.inline_query.answer(results)

def main(stop_event):
#def main():
	GamesController.init() #Call only once
	#initialize_testdata()

	#Init DB Create tables if they don't exist   
	log.info('Init DB in MultiGames Bot')
	try:
		conn = psycopg.connect(
			dbname=url.path[1:],
			user=url.username,
			password=url.password,
			host=url.hostname,
			port=url.port,
			connect_timeout=5
		)
		log.info('BD inicializada')
		conn.autocommit = True
		cur = conn.cursor()
		cur.execute(open("DBCreate.sql", "r").read())
		log.info('DB Created/Updated')
		conn.autocommit = False
	except Exception as e:
		log.error(f'Database connection failed: {e}')
		raise
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
	
	app = Application.builder().token(os.environ.get('TOKEN_MULTIGAMES')).build()

	# on different commands - answer in Telegram
	app.add_handler(CommandHandler("start", Commands.command_start))
	app.add_handler(CommandHandler("help", Commands.command_help))
	app.add_handler(CommandHandler("board", Commands.command_board))
	app.add_handler(CommandHandler("rules", Commands.command_rules))
	app.add_handler(CommandHandler("symbols", Commands.command_symbols))
	app.add_handler(CommandHandler("players", Commands.command_jugadores))
	app.add_handler(CommandHandler("newgame", Commands.command_newgame))
	app.add_handler(CommandHandler("startgame", Commands.command_startgame))
	app.add_handler(CommandHandler("delete", Commands.command_cancelgame))
	app.add_handler(CommandHandler("join", Commands.command_join))
	app.add_handler(CommandHandler("leave", Commands.command_leave))
	app.add_handler(CommandHandler("history", Commands.command_showhistory))
	app.add_handler(CommandHandler("ping", Commands.call_players_group))
	app.add_handler(CommandHandler("call", Commands.command_call))
	app.add_handler(CommandHandler("claim", Commands.command_claim))	
	app.add_handler(CommandHandler("prueba", Commands.command_prueba))	
	# Comando para mandar mensajes al equipo
	app.add_handler(CommandHandler("team", Commands.command_team))
	app.add_handler(CommandHandler("kick", Commands.command_kick))
	app.add_handler(CommandHandler("debug", Commands.command_toggle_debugging))
	
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosegameCHAT\*(.*)\*([0-9]*)", callback=Commands.callback_choose_game_chat))

	# Comando para hacer comandos sql desde el chat
	app.add_handler(CommandHandler("comando", Commands.command_newgame_sql_command))
	app.add_handler(CommandHandler("hojaayuda", Commands.command_hoja_ayuda))
	app.add_handler(CommandHandler("reglas", Commands.command_reglas))	
	app.add_handler(CommandHandler("save", Commands.save_comm))
	app.add_handler(CommandHandler("load", Commands.load))
	app.add_handler(CommandHandler("reload", Commands.reload))
	# Comando para preguntar los juegos que esperan mi accion.
	app.add_handler(CommandHandler("myturn", Commands.command_myturn))
	app.add_handler(CommandHandler("myturns", Commands.command_myturns))
	app.add_handler(CommandHandler("pass", Commands.command_pass))
	app.add_handler(CommandHandler("info", Commands.command_info))
	app.add_handler(CommandHandler("admin", Commands.command_admin_games))
	app.add_handler(CommandHandler("adminmenu", Commands.command_admin_menu))

	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*adminMenuOpc\*(.*)\*(-?[0-9]*)", callback=Commands.callback_admin_menu_opc))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*adminMenuTipo\*(.*)\*(-?[0-9]*)", callback=Commands.callback_admin_menu_tipo))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*adminMenuStats\*(.*)\*(-?[0-9]*)", callback=Commands.callback_admin_menu_stats))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*adminMenuGameList\*(.*)\*(-?[0-9]*)", callback=Commands.callback_admin_menu_game_list))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*adminMenuGameDelete\*(.*)\*(-?[0-9]*)", callback=Commands.callback_admin_menu_game_delete))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*adminMenuGameHistory\*(.*)\*(-?[0-9]*)", callback=Commands.callback_admin_menu_game_history))

	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*chooseGameInfo\*(.*)\*(-?[0-9]*)", callback=Commands.callback_info))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*chooseGameDelete\*(.*)\*(-?[0-9]*)", callback=Commands.callback_game_delete))
	
	# Configuracion de cualquier partida configurar para cada juego
	app.add_handler(CommandHandler("config", Commands.command_configurar_partida))
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosegame\*(.*)\*([0-9]*)", callback=Commands.callback_choose_game))
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosemode\*(.*)\*([0-9]*)", callback=Commands.callback_choose_mode))
	app.add_handler(CommandHandler("guess", Commands.command_guess))
	app.add_handler(CommandHandler("pass", Commands.command_pass))	
	
	# Herramientas de ADMIN
	app.add_handler(CommandHandler("ann", Commands.command_announce))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*announce\*(.*)\*(-?[0-9]*)", callback=callback_announce))
	app.add_handler(CommandHandler("setconfig", Commands.command_set_config_data))
	app.add_handler(CommandHandler("setstate", Commands.command_changestate))
	
	# Controller de Timers
	app.add_handler(CommandHandler('timer', Commands.callback_timer))
	
	# Lost Expedition Commands
	app.add_handler(CommandHandler("newgamelostexpedition", LostExpeditionCommands.command_newgame_lost_expedition))
	app.add_handler(CommandHandler("drawcard", LostExpeditionCommands.command_drawcard))
	app.add_handler(CommandHandler("showhand", LostExpeditionCommands.command_showhand))
	app.add_handler(CommandHandler("losebullet", LostExpeditionCommands.command_losebullet))
	app.add_handler(CommandHandler("gainbullet", LostExpeditionCommands.command_gainbullet))
	app.add_handler(CommandHandler("losefood", LostExpeditionCommands.command_losefood))
	app.add_handler(CommandHandler("gainfood", LostExpeditionCommands.command_gainfood))        
	app.add_handler(CommandHandler("stats", LostExpeditionCommands.command_showstats))
	app.add_handler(CommandHandler("campero", LostExpeditionCommands.command_vida_explorador_campero))
	app.add_handler(CommandHandler("brujula", LostExpeditionCommands.command_vida_explorador_brujula))
	app.add_handler(CommandHandler("hoja", LostExpeditionCommands.command_vida_explorador_hoja))
	app.add_handler(CommandHandler("addrutefromhand", LostExpeditionCommands.command_add_exploration))
	app.add_handler(CommandHandler("addrutefromdeck", LostExpeditionCommands.command_add_exploration_deck))
	app.add_handler(CommandHandler("addrutefromhandfirst", LostExpeditionCommands.command_add_exploration_first))
	app.add_handler(CommandHandler("moverutefirst", LostExpeditionCommands.command_add_exploration_deck_first))
	app.add_handler(CommandHandler("swaprute", LostExpeditionCommands.command_swap_exploration))
	app.add_handler(CommandHandler("removerute", LostExpeditionCommands.command_remove_exploration))
	app.add_handler(CommandHandler("removelastrute", LostExpeditionCommands.command_remove_last_exploration))
	app.add_handler(CommandHandler("showrute", LostExpeditionCommands.command_show_exploration))
	app.add_handler(CommandHandler("sortrute", LostExpeditionCommands.command_sort_exploration_rute))
	app.add_handler(CommandHandler("sorthand", LostExpeditionCommands.command_sort_hand))
	app.add_handler(CommandHandler("showskills", LostExpeditionCommands.command_showskills))
	app.add_handler(CommandHandler("gainprogreso", LostExpeditionCommands.command_increase_progreso))
	app.add_handler(CommandHandler("removefirstrute", LostExpeditionCommands.command_resolve_exploration))
	app.add_handler(CommandHandler("gainskill", LostExpeditionCommands.command_gain_skill))
	app.add_handler(CommandHandler("useskill", LostExpeditionCommands.command_use_skill))
	app.add_handler(CommandHandler("losecamp", LostExpeditionCommands.command_lose_camp))
	app.add_handler(CommandHandler("losecompass", LostExpeditionCommands.command_lose_compass))
	app.add_handler(CommandHandler("loseleaf", LostExpeditionCommands.command_lose_leaf))
	app.add_handler(CommandHandler("loseexplorer", LostExpeditionCommands.command_lose_explorer))
	app.add_handler(CommandHandler("resolve", LostExpeditionCommands.command_resolve_exploration2))
	app.add_handler(CommandHandler("dia", LostExpeditionCommands.command_worflow))
	app.add_handler(CommandHandler("noche", LostExpeditionCommands.command_worflow))
	# Lost Expedition Callbacks de botones
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*exe\*([^_]*)\*(.*)\*([0-9]*)", callback=LostExpeditionCommands.execute_command))
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*opcioncomandos\*(.*)\*([0-9]*)", callback=LostExpeditionCommands.elegir_opcion_comando))
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*opcionskill\*(.*)\*([0-9]*)", callback=LostExpeditionCommands.elegir_opcion_skill))	
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*commando\*([^_]*)\*swap\*([0-9]*)", callback=LostExpeditionCommands.callback_choose_swap))
			
	# Handlers de JustOne
	#app.add_handler(CommandHandler("guess", JustoneCommands.command_guess))
	#app.add_handler(CommandHandler("pass", JustoneCommands.command_pass))	
	app.add_handler(CommandHandler("clue", JustoneCommands.command_clue))
	# Just One Callbacks de botones
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosedicc\*(.*)\*([0-9]*)", callback=JustOneController.callback_finish_config_justone))	
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*rechazar\*([0-9]*)", callback=JustOneController.callback_review_clues))
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*finalizar\*(.*)\*([0-9]*)", callback=JustOneController.callback_review_clues_finalizado))
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*reviewerconfirm\*(.*)\*([0-9]*)", callback=JustOneController.callback_reviewer_confirm))
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosegameclue\*(.*)\*([0-9]*)", callback=JustoneCommands.callback_choose_game_clue))
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*chooseend\*(.*)\*([0-9]*)", callback=JustOneController.callback_finish_game_buttons))
	
	# Handlers de SayAnything
	app.add_handler(CommandHandler("resp", SayAnythingCommands.command_propose))
	app.add_handler(CommandHandler("pick", Commands.command_pick))
	# Say Anything Callbacks de botones
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosediccSA\*(.*)\*([0-9]*)", callback=SayAnythingController.callback_finish_config))
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosegamepropSA\*(.*)\*([0-9]*)", callback=SayAnythingCommands.callback_choose_game_prop))
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*chooseendSA\*(.*)\*([0-9]*)", callback=SayAnythingController.callback_finish_game_buttons))
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosegamepickSA\*(.*)\*([0-9]*)", callback=SayAnythingCommands.callback_choose_game_pick))
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*voteRespuestaSA\*(.*)\*([0-9]*)", callback=SayAnythingController.callback_put_vote))
	
	# Handlers de Arcana
	# Arcana Callbacks de botones
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosediccAR\*(.*)\*([0-9]*)", callback=ArcanaController.callback_finish_config))
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*txtArcanaAR\*(.*)\*([0-9]*)", callback=ArcanaController.callback_txt_arcana))
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*chooseFateAR\*(.*)\*([0-9]*)", callback=ArcanaController.callback_choose_fate))
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*chooseArcanaAR\*(.*)\*([0-9]*)", callback=ArcanaController.callback_choose_arcana))
	app.add_handler(CommandHandler("remove", ArcanaCommands.command_remove))	
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*chooseendAR\*(.*)\*([0-9]*)", callback=ArcanaController.callback_finish_game_buttons))
	app.add_handler(CommandHandler("discard", ArcanaCommands.command_discard))	
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*([A-Za-z]*)ArcanaAC\*(.*)\*(-?[0-9]*)", callback=ArcanaController.callback_choose_arcana_action))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*([A-Za-z]*)FateAC\*(.*)\*(-?[0-9]*)", callback=ArcanaController.callback_choose_fate_action))
	
	# Handlers de Wavelength
	app.add_handler(CommandHandler("ref", WavelengthCommands.command_reference))
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosegamerefWL\*(.*)\*([0-9]*)", callback=WavelengthCommands.callback_choose_game_prop))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*([A-Za-z]*)Wave\*(.*)\*(.*)", callback=WavelengthCommands.callback_Wave))
	app.add_handler(CommandHandler("draw", WavelengthCommands.command_draw))
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*chooseendWL\*(.*)\*([0-9]*)", callback=WavelengthController.callback_finish_game_buttons))
	
	
	# Handlers de Decrypt
	app.add_handler(CommandHandler("code", DecryptCommands.command_code))
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosegamerefDE\*(.*)\*([0-9]*)", callback=DecryptCommands.callback_choose_game_prop))
	#app.add_handler(CallbackQueryHandler(pattern="(-?[0-9]*)\*([A-Za-z]*)Wave\*(.*)\*(.*)", callback=DecryptCommands.callback_Wave))
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosediccDE\*(.*)\*([0-9]*)", callback=DecryptController.callback_finish_config_decrypt))
	
	app.add_handler(CommandHandler("intercept", DecryptCommands.command_intercept))
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosegameintDE\*(.*)\*([0-9]*)", callback=DecryptCommands.callback_choose_game_inter))
	
	app.add_handler(CommandHandler("decrypt", DecryptCommands.command_decrypt))
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosegamedecDE\*(.*)\*([0-9]*)", callback=DecryptCommands.callback_choose_game_dec))
	
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*chooseendDE\*(.*)\*([0-9]*)", callback=DecryptController.callback_finish_game_buttons))
	
	#app.add_handler(CommandHandler("decrypt", DecryptCommands.command_decrypt))

	# Handlers de Werewords
	app.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_moduloWW_(.*)", callback=WerewordsController.incluir_modulo))
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosediccWW\*(.*)\*([0-9]*)", callback=WerewordsController.callback_finish_config_werewords))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*choosemagicwordWW\*(.*)\*(-?[0-9]*)", callback=WerewordsController.callback_choose_magic_word))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*choosepokeWW\*(.*)\*(-?[0-9]*)", callback=WerewordsController.callback_choose_poke))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*choosedopleWW\*(.*)\*(-?[0-9]*)", callback=WerewordsController.callback_choose_dople))
	app.add_handler(CommandHandler("ask", WerewordsCommands.command_ask))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*askWW\*(.*)\*(-?[0-9]*)", callback=WerewordsController.callback_ask))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*choosevidenteWW\*(.*)\*(-?[0-9]*)", callback=WerewordsController.callback_choose_vidente))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*chooseloboWW\*(.*)\*(-?[0-9]*)", callback=WerewordsController.callback_choose_lobo))
	app.add_handler(CommandHandler("toofar", WerewordsCommands.command_toofar))
	app.add_handler(CommandHandler("soclose", WerewordsCommands.command_soclose))
	app.add_handler(CommandHandler("undo", WerewordsCommands.command_undo))
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*chooseendWW\*(.*)\*([0-9]*)", callback=WerewordsController.callback_finish_game_buttons))

	# Handlers de Deception
	app.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_moduloDC_(.*)", callback=DeceptionController.incluir_modulo))
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosediffDC\*(.*)\*([0-9]*)", callback=DeceptionController.callback_finish_config_werewords))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*choosemotivoDC\*(.*)\*(-?[0-9]*)", callback=DeceptionController.callback_choose_motivo))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*choosepistaDC\*(.*)\*(-?[0-9]*)", callback=DeceptionController.callback_choose_pista))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*choosecontinueDayDC\*(.*)\*(-?[0-9]*)", callback=DeceptionController.callback_choose_continue))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*chooseforensicDC\*(.*)\*(-?[0-9]*)", callback=DeceptionController.callback_choose_forensic))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*chooseforensicdetailDC\*(.*)\*(-?[0-9]*)", callback=DeceptionController.callback_choose_forensic_detail))
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*chooseAccuseDE\*(.*)\*([0-9]*)", callback=DeceptionController.callback_accuse))
	#.add_handler(CommandHandler("undo", DeceptionCommands.command_undo))
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*chooseendDC\*(.*)\*([0-9]*)", callback=DeceptionController.callback_finish_game_buttons))

	app.add_handler(CommandHandler("newevidence", DeceptionCommands.command_evidence_collection))
	app.add_handler(CommandHandler("accuse", DeceptionCommands.command_accuse))

	# Unanimo Comandos y Callbacks de botones
	app.add_handler(CommandHandler("words", UnanimoCommands.command_words))
	app.add_handler(CommandHandler("points", UnanimoCommands.command_points))
	
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosediccUnanimo\*(.*)\*([0-9]*)", callback=UnanimoController.callback_finish_config_unanimo))
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosegamewords\*(.*)\*([0-9]*)", callback=UnanimoCommands.callback_choose_game_clue))
	# app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*rechazar\*([0-9]*)", callback=JustOneController.callback_review_clues))
	# app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*finalizar\*(.*)\*([0-9]*)", callback=JustOneController.callback_review_clues_finalizado))
	# app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*reviewerconfirm\*(.*)\*([0-9]*)", callback=JustOneController.callback_reviewer_confirm))
	# app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosegameclue\*(.*)\*([0-9]*)", callback=JustoneCommands.callback_choose_game_clue))
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*chooseendunanimo\*(.*)\*([0-9]*)", callback=UnanimoController.callback_finish_game_buttons))

	# Handlers de SecretoCodigo
	app.add_handler(CommandHandler("hint", SecretoCodigoCommands.command_hint))
	app.add_handler(CommandHandler("endturn", SecretoCodigoCommands.command_endturn))
	app.add_handler(CommandHandler("demotablero", SecretoCodigoCommands.command_demotablero))
	app.add_handler(CommandHandler("demotablero2", SecretoCodigoCommands.command_demotablero2))
	app.add_handler(CommandHandler("demotablero3", SecretoCodigoCommands.command_demotablero3))
	app.add_handler(CommandHandler("pickb", SecretoCodigoCommands.command_pickb))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*pickb\*([0-9]*)\*([0-9]*)", callback=SecretoCodigoCommands.callback_pickb))
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosediccCN\*(.*)\*([0-9]*)", callback=SecretoCodigoController.callback_finish_config_cn))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*choosegamehintCN\*(.*)\*([0-9]*)", callback=SecretoCodigoCommands.callback_choose_game_hint_cn))
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*chooseendCN\*(.*)\*([0-9]*)", callback=SecretoCodigoController.callback_finish_game_buttons_cn))

	# Handlers de SpyFall
	app.add_handler(CommandHandler("acusar", SpyFallCommands.command_acusar))
	app.add_handler(CommandHandler("adivinar", SpyFallCommands.command_adivinar))
	app.add_handler(CommandHandler("rol", SpyFallCommands.command_rol))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*spyfallVoto\*(-?[0-9]*)\*(-?[0-9]*)", callback=SpyFallCommands.callback_spyfall_voto))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*spyfallAdivinar\*([0-9]*)\*(-?[0-9]*)", callback=SpyFallCommands.callback_spyfall_adivinar))
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*chooseendSpy\*(.*)\*([0-9]*)", callback=SpyFallController.callback_finish_game_buttons_spy))

	# Handlers de Insider
	app.add_handler(CommandHandler("acerto", InsiderCommands.command_acerto))
	app.add_handler(CommandHandler("notiempo", InsiderCommands.command_notiempo))
	app.add_handler(CommandHandler("palabra", InsiderCommands.command_palabra))
	app.add_handler(CommandHandler("mirol", InsiderCommands.command_rol))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*insiderAcerto\*(-?[0-9]*)\*(-?[0-9]*)", callback=InsiderCommands.callback_insider_acerto))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*insiderJuzgar\*(si|no)\*([0-9]*)", callback=InsiderCommands.callback_insider_juzgar))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*insiderVotar\*(-?[0-9]*)\*([0-9]*)", callback=InsiderCommands.callback_insider_votar))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*insiderDesempate\*(-?[0-9]*)\*(-?[0-9]*)", callback=InsiderCommands.callback_insider_desempate))
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*chooseendInsider\*(.*)\*([0-9]*)", callback=InsiderController.callback_finish_game_buttons_insider))

	# Handlers de Battlestar Galactica
	app.add_handler(CommandHandler("lealtad", BSGCommands.command_lealtad))
	app.add_handler(CommandHandler("mano", BSGCommands.command_mano))
	app.add_handler(CommandHandler("estado", BSGCommands.command_estado))
	app.add_handler(CommandHandler("accion", BSGCommands.command_accion))
	app.add_handler(CommandHandler("mover", BSGCommands.command_mover))
	app.add_handler(CommandHandler("crisis", BSGCommands.command_crisis))
	app.add_handler(CommandHandler("aportar", BSGCommands.command_aportar))
	app.add_handler(CommandHandler("resolver", BSGCommands.command_resolver))
	app.add_handler(CommandHandler("revelar", BSGCommands.command_revelar))
	app.add_handler(CommandHandler("habilidad", BSGCommands.command_habilidad))
	app.add_handler(CommandHandler("quorum", BSGCommands.command_quorum))
	app.add_handler(CommandHandler("encarcelar", BSGCommands.command_encarcelar))
	app.add_handler(CommandHandler("liberar", BSGCommands.command_liberar))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*bsgPick\*([a-z_]*)\*(-?[0-9]*)", callback=BSGCommands.callback_bsg_pick))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*bsgAccion\*([a-z0-9_]*)\*(-?[0-9]*)", callback=BSGCommands.callback_bsg_accion))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*bsgMover\*([a-z_]*)\*(-?[0-9]*)", callback=BSGCommands.callback_bsg_mover))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*bsgCylon\*([a-z0-9_]*)\*(-?[0-9]*)", callback=BSGCommands.callback_bsg_cylon))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*bsgBrig\*(-?[0-9]*)\*(-?[0-9]*)", callback=BSGCommands.callback_bsg_brig))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*bsgFree\*(-?[0-9]*)\*(-?[0-9]*)", callback=BSGCommands.callback_bsg_free))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*bsgQuorum\*([0-9]*)\*(-?[0-9]*)", callback=BSGCommands.callback_bsg_quorum))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*bsgEleccion\*([0-9]*)\*(-?[0-9]*)", callback=BSGCommands.callback_bsg_eleccion))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*bsgCrisisOpt\*([a-z]*)\*(-?[0-9]*)", callback=BSGCommands.callback_bsg_crisis_opt))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*bsgCrisisVoto\*([0-9]*)\*(-?[0-9]*)", callback=BSGCommands.callback_bsg_crisis_voto))
	app.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*bsgTarget\*([a-z0-9_]*)\*(-?[0-9]*)", callback=BSGCommands.callback_bsg_target))
	app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*chooseendBSG\*(.*)\*([0-9]*)", callback=BSGController.callback_finish_game_buttons_bsg))

	app.add_handler(CommandHandler("status", command_status))

	# WEb Crapping commands
	app.add_handler(CommandHandler("news", Commands.command_noticias))
	app.add_handler(CommandHandler("imagen", Commands.command_image))
	# Handlers de D100
	app.add_handler(CommandHandler("tirada", Commands.command_roll))
	
	app.add_handler(CommandHandler('put', put))	
	app.add_handler(CommandHandler('get', get))	
	
	app.add_handler(MessageHandler(filters.COMMAND, unknown))
	app.add_handler(MessageHandler(filters.TEXT, command_status))
	
	# Handler cuando se una una persona al chat.
	#app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, add_group))
	
	# Handler cuando se va una persona del chat.
	#app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, remove_group))
	
	# Handler cuando se cambia el nombre del chat 
	app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_TITLE, change_groupname))

	app.add_handler(MessageHandler(filters.StatusUpdate.MIGRATE, change_group_id))

	# Inline query
	app.add_handler(InlineQueryHandler(inlinequery))		
	
	job_que = app.job_queue
	
	if job_que is not None:
		morning = datetime.time(14, 48, 0, 0, tzinfo=pytz.timezone("America/Argentina/Buenos_Aires"))
		job_que.run_daily(repeat_test, morning)
		# job_que.start()
	else:
		log.warning('JobQueue not available. Install with: pip install "python-telegram-bot[job-queue]"')

	# log all errors
	app.add_error_handler(error)
	
	app.post_init = notify_startup

	# Start the Bot
	# app.run_polling(timeout=30)

	while not stop_event.is_set():
		app.run_polling(timeout=5, stop_signals=None)  # short timeout so loop checks stop_event often

	#asyncio.run(app.bot.send_message(ADMIN[0], "Nueva version en linea"))

async def notify_startup(application: Application):
    await application.bot.send_message(
        chat_id=ADMIN[0],
        text="✅ Nueva versión en línea"
    )


if __name__ == '__main__':
    main()
