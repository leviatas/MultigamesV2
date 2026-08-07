from ast import arg
import json
import logging as log
import datetime
import random
#import ast
import jsonpickle
import os
import psycopg2
from psycopg2 import sql
import urllib.parse

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.ext import (CallbackContext)
import re
from collections import namedtuple

import SecretHitler.MainController as MainController
import SecretHitler.GamesController as GamesController
from SecretHitler.Constants.Config import ADMIN, VERSION
from SecretHitler.Constants.Cards import opciones_choose_posible_role, playerSets
from SecretHitler.Boardgamebox.Board import Board
from SecretHitler.Boardgamebox.Game import Game
from SecretHitler.Boardgamebox.Player import Player
from SecretHitler.Boardgamebox.State import State
from SecretHitler.PlayerStats import PlayerStats
from SecretHitler.EstadisticsCalculator import PrintEstadisticas
import SecretHitler.StatsExtended as StatsExtended
import SecretHitler.Achievements as Achievements
# Enable logging

log.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=log.INFO)
logger = log.getLogger(__name__)

#DB Connection I made a Haroku Postgres database first
urllib.parse.uses_netloc.append("postgres")
url = urllib.parse.urlparse(os.environ["DATABASE_URL"])


commands = [  # command description used in the "help" command
    '/help - Te da informacion de los comandos disponibles',
    '/start - Da un poco de información sobre Secret Hitler',
    '/symbols - Te muestra todos los símbolos posibles en el tablero',
    '/rules - Te da un link al sitio oficial con las reglas de Secret Hitler',
    '/newgame - Crea un nuevo juego o carga un juego previo',
    '/join - Te une a un juego existente',
    '/startgame - Comienza un juego existente cuando todos los jugadores se han unido',
    '/cancelgame - Cancela un juego existente, todos los datos son borrados.',
    '/board - Imprime el tablero actual con la pista liberal y la pista fascista, orden presidencial y contador de elección',
    '/history - Imprime el historial del juego actual',
    '/votes - Imprime quien ha votado',
    '/calltovote - Avisa a los jugadores que se tiene que votar (o que falten votar el MVP si la partida ya terminó)',
    '/retirar - Retira tu voto de Ja o Nein para poder votar de nuevo',
    '/startautoja - Activa tu voto automático Ja apenas se proponga una fórmula (fuera de Zona Hitler)',
    '/stopautoja - Desactiva tu voto automático Ja',
    '/logros - Muestra tus logros desbloqueados',
    '/guess - Adivina en privado quiénes son los fascistas y Hitler',
    '/mvp - Vota en privado al mejor jugador de la partida',
    '/end - Cierra la votación de MVP sin esperar a que voten todos',
    '/version - Muestra la versión actual del bot'
]

symbols = [
    u"\u25FB\uFE0F" + ' Lugar vacio sin poder especial',
    u"\u2716\uFE0F" + ' Campo cubierto con una carta',  # X
    u"\U0001F52E" + ' Poder Presidencial: Investigar Políticas',  # crystal
    u"\U0001F50E" + ' Poder Presidencial: Investigar Afiliación Política',  # inspection glass
    u"\U0001F5E1" + ' Poder Presidencial: Ejecución',  # knife
    u"\U0001F454" + ' Poder Presidencial: Llamar a Elección Especial',  # tie
    u"\U0001F54A" + ' Liberales ganan',  # dove
    u"\u2620" + ' Fascistas ganan'  # skull
]

def get_game(cid):
	# Busco el juego actual
	game = GamesController.games.get(cid, None)	
	if game:
		# Si esta lo devuelvo.
		return game
	else:
		# Si no esta lo busco en BD y lo pongo en GamesController.games
		game = load_game(cid)
		if game:
			GamesController.games[cid] = game
			return game
		else:
			None

def command_symbols(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	symbol_text = "Los siguientes símbolos aparecen en el tablero: \n"
	for i in symbols:
		symbol_text += i + "\n"
	bot.send_message(cid, symbol_text)


def command_board(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	game = get_game(cid)
	if game:		
		if game.board:			
			print_board(bot, game, cid)
		else:
			bot.send_message(cid, "No hay juego comenzado en este chat.  Por favor comience el juego con /startgame")
	else:
		bot.send_message(cid, "No hay juego en este chat. Crea un nuevo juego con /newgame")

def print_board(bot, game, target):
	bot.send_message(target, game.board.print_board(game.player_sequence), ParseMode.MARKDOWN)
		
def command_start(update: Update, context: CallbackContext):
	bot = context.bot

	cid = update.message.chat_id
	bot.send_message(cid,
		     "\"Secret Hitler es un juego de deducción social para 5-10 jugadores "
		     "acerca de encontrar a Hitler y detener el ascenso del fascismo."
		     " La mayoría de los jugadores son liberales. Si pueden aprender a "
		     "confiar entre ellos, tienen suficientes votos para controlar el parlamento y ganar el juego."
		     " Pero algunos jugadores son fascistas. Ellos dirán lo que sea necesario para ser electos, "
		     "promover el fascismo y culpar a los demás por la derrota de la República."
		     " Los liberales deben trabajar juntos para descubrir la verdad antes "
		     "de que los fascistas instalen a su desalamado líder y ganen el juego."
		     " Traducción de la descripición oficial de Secret Hitler."
		     " Agregame a un grupo y escribe /newgame para crear un juego!")
	command_help(update, context)


def command_rules(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id	
	msg = """En cada turno el jugador activo, *Presidente* de ahora en más, elige un jugador como su *canciller*.
	Luego todos los jugadores votan si aceptan la formula elegida.
	Si hay mayoria de votos *JA!* (positivos) la formula se convierte en activa.
	En ese caso el jugador *presidente* recibe 3 cartas del mazo de politicas, este esta compuesto inicialmente por
	*11 Politicas fascistas*
	*6 Politicas liberales*
	Al recibir las cartas el presidente recibirá en privado una botonera con las 3 cartas y se le pedirá que
	*DESCARTE* una de ellas para pasar las dos restantes al canciller.
	El canciller recibirá las dos politicas restantes y eligirá una para promulgar.
	
	El objetivo de los fascistas es promulgar *6 politicas fascistas* o *3 y que Hitler sea elegido canciller*.
	EL objetivo de los liberales es promulgar *5 politicas liberales* o *Matar a Hitler*
	
	Si se promulga una politica fascista hay posibilidad que haya una acción para el *presidente* relacionada a ella.
	/symbols Da un resumen de que hace cada acción.
	"""
	bot.send_message(cid, msg, ParseMode.MARKDOWN)


# pings the bot
def command_ping(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	bot.send_message(cid, 'pong - v0.3')

def command_version(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	bot.send_message(cid, "Secret Hitler bot v%s" % VERSION)


def get_stat_query(query, partidas_totales, partidas_fascista, partidas_hitler, partidas_liberal, partidas_murio, partidas_fascista_gano, partidas_hitler_gano, partidas_liberal_gano):
	conn = psycopg2.connect(
		database=url.path[1:],
		user=url.username,
		password=url.password,
		host=url.hostname,
		port=url.port
	)
	cursor = conn.cursor()
	cursor.execute(query)
	if cursor.rowcount > 0:
		for table in cursor.fetchall():
			game_endcode = table[0]
			# Sumo las partidas independiente de que rol era.
			partidas_totales += (table[1] + table[2] + table[3])
			# Cuento las aprtidas con ciertos roles
			partidas_fascista += table[1]
			partidas_hitler += table[2]
			partidas_liberal += table[3]

			if game_endcode == 1 or game_endcode == 2:
				partidas_liberal_gano += table[3]
			if game_endcode == -1 or game_endcode == -2:
				partidas_fascista_gano += table[1]
				partidas_hitler_gano += table[2]
	conn.close()
	return partidas_totales, partidas_fascista, partidas_hitler, partidas_liberal, partidas_murio, partidas_fascista_gano, partidas_hitler_gano, partidas_liberal_gano
	
# prints statistics, only ADMIN
def command_stats(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	cid, uid = update.message.chat_id, update.message.from_user.id	
	
	if len(args) > 0:
		# Primero hare estadisticas de Personas
			
		partidas_totales = 0
		partidas_fascista = 0
		partidas_hitler = 0
		partidas_liberal = 0
		partidas_murio = 0
		partidas_fascista_gano = 0
		partidas_hitler_gano = 0
		partidas_liberal_gano = 0
		
		try:
			#Check if game is in DB first			
			jugador = ' '.join(args)			
			replace_dead = "regexp_replace(playerlist, ' \(dead\)| \(muerto\)', '', 'g')"			
			
			query = "SELECT x.game_endcode, COUNT(CASE " \
				"WHEN {1} like '%%{0} secret role was Fasc%%' then x.game_endcode end" \
				")," \
				"COUNT(CASE " \
				"WHEN {1} like '%%{0} secret role was Hitl%%' then x.game_endcode end" \
				")," \
				"COUNT(CASE " \
				"WHEN {1} like '%%{0} secret role was Libe%%' then x.game_endcode end" \
				") " \
				"FROM stats_detail_secret_hitler x WHERE " \
				"{1} like '%%{0} secret role was%%' GROUP BY game_endcode" \
				.format(jugador, replace_dead)
			
			query2 = "SELECT x.game_endcode, COUNT(CASE " \
				"WHEN {1} like '%%El rol de {0} era Fasc%%' then x.game_endcode end" \
				")," \
				"COUNT(CASE " \
				"WHEN {1} like '%%El rol de {0} era Hitl%%' then x.game_endcode end" \
				")," \
				"COUNT(CASE " \
				"WHEN {1} like '%%El rol de {0} era Libe%%' then x.game_endcode end" \
				") " \
				"FROM stats_detail_secret_hitler x WHERE " \
				"{1} like '%%El rol de {0} era%%' GROUP BY game_endcode" \
				.format(jugador, replace_dead)
			
			partidas_totales, partidas_fascista, partidas_hitler, partidas_liberal, partidas_murio, partidas_fascista_gano,	partidas_hitler_gano, partidas_liberal_gano = get_stat_query(query, partidas_totales, partidas_fascista, partidas_hitler, partidas_liberal, partidas_murio, partidas_fascista_gano, partidas_hitler_gano, partidas_liberal_gano)
			partidas_totales, partidas_fascista, partidas_hitler, partidas_liberal, partidas_murio, partidas_fascista_gano,	partidas_hitler_gano, partidas_liberal_gano = get_stat_query(query2, partidas_totales, partidas_fascista, partidas_hitler, partidas_liberal, partidas_murio, partidas_fascista_gano, partidas_hitler_gano, partidas_liberal_gano)
						
			if partidas_totales > 0:											
				query = "select count(*) FROM stats_detail_secret_hitler x where x.playerlist like '%%{0} (dead)%%' or x.playerlist like '%%{0} (muerto)%%'".format(jugador)
				
				conn = psycopg2.connect(
					database=url.path[1:],
					user=url.username,
					password=url.password,
					host=url.hostname,
					port=url.port
				)
				cursor = conn.cursor()
				cursor.execute(query)
				datamurio = cursor.fetchone()
				partidas_murio += datamurio[0]
				
				bot.send_message(cid, 'Resultado de la consulta:')
				stattext = "+++ Estadísticas *{0}* +++\n".format(jugador) + \
					"Partidas Jugadas: *{0}*\n".format(partidas_totales) + \
					"Partidas como liberal: *{1}/{0}* Ganó: *{2}/{1}*\n".format(partidas_totales, partidas_liberal, partidas_liberal_gano) + \
					"Partidas como Fascista:  *{1}/{0}* Ganó: *{2}/{1}*\n".format(partidas_totales, partidas_fascista, partidas_fascista_gano) + \
					"Partidas como Hitler:  *{1}/{0}* Ganó: *{2}/{1}*\n".format(partidas_totales, partidas_hitler, partidas_hitler_gano) + \
					"Partidas que ganó:  *{1}/{0}* {2:.2f}%\n".format(partidas_totales, (partidas_hitler_gano+partidas_fascista_gano+partidas_liberal_gano), (partidas_hitler_gano+partidas_fascista_gano+partidas_liberal_gano) / (partidas_totales/100) ) + \
					"Partidas que murió:  *{1}/{0}*\n".format(partidas_totales, partidas_murio)	
				conn.close()
				bot.send_message(cid, stattext, ParseMode.MARKDOWN)
			else:
				bot.send_message(cid, 'No se obtuvo nada de la consulta')
			
		except Exception as e:
			bot.send_message(cid, 'No se ejecuto el comando debido a: '+str(e))
	else:
		# Si el usuario no pone argumentos se muestran las estadisticas normales
		stats = MainController.get_stats(bot, cid)		
		stattext = "+++ Estadísticas +++\n" + \
				"Vict. Liberal (Politicas): *" + str(stats[3]) + "*\n" + \
				"Vict. Liberal (Hitler ☠): *" + str(stats[4]) + "*\n" + \
				"Vict. Fascista (Politicas): *" + str(stats[2]) + "*\n" + \
				"Vict. Fascista (Hitler Canc): *" + str(stats[1]) + "*\n" + \
				"Juegos cancelados: *" + str(stats[5]) + "*\n" + \
				"Juegos totales: *" + str(stats[1] + stats[2] + stats[3] + stats[4]) + "*\n\n"		
		bot.send_message(cid, stattext, ParseMode.MARKDOWN)

# estadisticas nuevas, vinculadas al uid de Telegram. Sin argumentos: las del que invoca.
# Con un nombre: busca ese nombre entre los uids registrados (si hay mas de uno, lista los IDs).
# Con un ID numerico: las de ese uid puntual.
def command_stats2(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	caller_uid = update.message.from_user.id
	args = context.args

	if len(args) == 0:
		target_uid = caller_uid
	elif len(args) == 1 and args[0].isdigit():
		target_uid = int(args[0])
	else:
		name = ' '.join(args)
		try:
			matches = StatsExtended.get_uids_by_name(name)
		except Exception as e:
			bot.send_message(cid, 'No se ejecuto el comando debido a: ' + str(e))
			return

		if not matches:
			bot.send_message(cid, "No hay estadisticas nuevas para nadie con el nombre '{0}'.".format(name))
			return
		if len(matches) > 1:
			lines = ["Hay más de un jugador con el nombre '{0}':".format(name)]
			for m_uid, m_name, total in matches:
				lines.append("- ID {0} ({1}): {2} partidas".format(m_uid, m_name, total))
			lines.append("\nUsá /stats2 <ID> para ver las estadísticas de uno en particular.")
			bot.send_message(cid, "\n".join(lines))
			return
		target_uid = matches[0][0]

	try:
		base = StatsExtended.get_base_stats_by_uid(target_uid)
		if base is None:
			quien = "vos" if target_uid == caller_uid else "el ID {0}".format(target_uid)
			bot.send_message(cid, "No hay estadisticas nuevas todavia para {0}. Pedile a un admin que use "
				"/vincularstats para vincular las partidas viejas, o que siga jugando para generar estadisticas nuevas.".format(quien))
			return

		kills = StatsExtended.get_kill_stats(target_uid)
		teammates = StatsExtended.get_teammate_stats(target_uid)
	except Exception as e:
		bot.send_message(cid, 'No se ejecuto el comando debido a: ' + str(e))
		return

	stattext = "+++ Estadísticas +++\n" + \
		"Partidas Jugadas: *{0}*\n".format(base["total"]) + \
		"Partidas como liberal: *{1}/{0}* Ganó: *{2}/{1}*\n".format(base["total"], base["liberal"], base["liberal_won"]) + \
		"Partidas como Fascista:  *{1}/{0}* Ganó: *{2}/{1}*\n".format(base["total"], base["fascista"], base["fascista_won"]) + \
		"Partidas como Hitler:  *{1}/{0}* Ganó: *{2}/{1}*\n".format(base["total"], base["hitler"], base["hitler_won"]) + \
		"Partidas que ganó:  *{1}/{0}* {2:.2f}%\n".format(base["total"], base["gano"], (base["gano"] / base["total"]) * 100) + \
		"Partidas que murió:  *{1}/{0}*\n".format(base["total"], base["murio"]) + \
		"\nGente que mató: *{0}*\n".format(kills["kills_count"])

	if kills["most_killed"]:
		_, victim_name, victim_count = kills["most_killed"]
		stattext += "A quién más mató: *{0}* ({1} veces)\n".format(victim_name, victim_count)
	if kills["most_frequent_killer"]:
		killer_name, killer_count = kills["most_frequent_killer"]
		stattext += "Quién más lo mató: *{0}* ({1} veces)\n".format(killer_name, killer_count)
	if teammates["best_teammates"]:
		names = ", ".join(n for n, c in teammates["best_teammates"])
		stattext += "Ganó más partidas con: *{0}* ({1} veces)\n".format(names, teammates["best_teammates"][0][1])
	if teammates["worst_teammates"]:
		names = ", ".join(n for n, c in teammates["worst_teammates"])
		stattext += "Perdió más partidas con: *{0}* ({1} veces)\n".format(names, teammates["worst_teammates"][0][1])

	bot.send_message(cid, stattext, ParseMode.MARKDOWN)

def command_logros(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	caller_uid = update.message.from_user.id
	caller_name = update.message.from_user.first_name or str(caller_uid)
	args = context.args

	if len(args) == 0:
		target_uid = caller_uid
		target_name = caller_name
	elif len(args) == 1 and args[0].isdigit():
		target_uid = int(args[0])
		target_name = str(target_uid)
	else:
		name = ' '.join(args)
		try:
			matches = StatsExtended.get_uids_by_name(name)
		except Exception as e:
			bot.send_message(cid, 'No se ejecuto el comando debido a: ' + str(e))
			return

		if not matches:
			bot.send_message(cid, "No hay estadisticas nuevas para nadie con el nombre '{0}'.".format(name))
			return
		if len(matches) > 1:
			lines = ["Hay más de un jugador con el nombre '{0}':".format(name)]
			for m_uid, m_name, total in matches:
				lines.append("- ID {0} ({1}): {2} partidas".format(m_uid, m_name, total))
			lines.append("\nUsá /logros <ID> para ver los logros de uno en particular.")
			bot.send_message(cid, "\n".join(lines))
			return
		target_uid, target_name, _ = matches[0]

	try:
		texto = Achievements.format_logros_message(target_uid, target_name)
	except Exception as e:
		bot.send_message(cid, 'No se ejecuto el comando debido a: ' + str(e))
		return

	bot.send_message(cid, texto, ParseMode.MARKDOWN)

# vincula partidas viejas (buscadas por nombre) a un uid de Telegram, solo ADMIN
def command_vincularstats(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	uid = update.message.from_user.id
	args = context.args

	if uid != ADMIN:
		return

	if len(args) < 2:
		bot.send_message(cid, "Uso: /vincularstats <id_telegram> <nombre>")
		return

	try:
		target_uid = int(args[0])
	except ValueError:
		bot.send_message(cid, "El primer argumento debe ser un ID de Telegram numérico.")
		return

	name = ' '.join(args[1:])

	bot.send_message(cid, "Comenzando a vincular las partidas viejas de '{0}' al ID {1}...".format(name, target_uid))

	try:
		linked = StatsExtended.migrate_legacy_stats(target_uid, name)
		bot.send_message(cid, "Se vincularon {0} partidas viejas de '{1}' al ID {2}.".format(linked, name, target_uid))
	except Exception as e:
		bot.send_message(cid, 'No se ejecuto el comando debido a: ' + str(e))

# vincula varios jugadores a la vez, parseando lineas tipo "User <nombre>'s ID is <id>.", solo ADMIN
_VINCULARSTATS2_LINE = re.compile(r"User\s+(.+?)'s\s+ID\s+is\s+(\d+)\.?", re.IGNORECASE)

def command_vincularstats2(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	uid = update.message.from_user.id

	if uid != ADMIN:
		return

	matches = _VINCULARSTATS2_LINE.findall(update.message.text)
	if not matches:
		bot.send_message(cid, "Uso: /vincularstats2 seguido de lineas como:\nUser <nombre>'s ID is <id>.")
		return

	bot.send_message(cid, "Comenzando a vincular {0} jugador(es)...".format(len(matches)))

	resultados = []
	for name, uid_str in matches:
		name = name.strip()
		target_uid = int(uid_str)
		try:
			linked = StatsExtended.migrate_legacy_stats(target_uid, name)
			resultados.append("{0} (ID {1}): {2} partidas vinculadas".format(name, target_uid, linked))
		except Exception as e:
			resultados.append("{0} (ID {1}): error - {2}".format(name, target_uid, str(e)))

	bot.send_message(cid, "\n".join(resultados))

def command_admin(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	uid = update.message.from_user.id
	if uid != ADMIN:
		return
	btns = [
		[InlineKeyboardButton("first", callback_data="admin_first")],
		[InlineKeyboardButton("cleanup mision imposible", callback_data="admin_cleanup_mision")],
	]
	markup = InlineKeyboardMarkup(btns)
	bot.send_message(cid, "🛠 *Panel de administración*", reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

def callback_admin_first(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_admin_first called')
	callback = update.callback_query
	uid = callback.from_user.id
	if uid != ADMIN:
		return
	try:
		nuevos_uids = Achievements.backfill_primera_partida()
	except Exception as e:
		bot.send_message(uid, "Error al correr el backfill: %s" % str(e))
		return
	if nuevos_uids:
		texto = "✅ Se otorgó *Primera vez* retroactivamente a {} jugador{}.".format(
			len(nuevos_uids), "" if len(nuevos_uids) == 1 else "es")
	else:
		texto = "✅ No había nadie pendiente, todos los que califican ya tenían el logro."
	bot.edit_message_text(texto, chat_id=callback.message.chat_id, message_id=callback.message.message_id,
		parse_mode=ParseMode.MARKDOWN)

def callback_admin_cleanup_mision(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_admin_cleanup_mision called')
	callback = update.callback_query
	uid = callback.from_user.id
	if uid != ADMIN:
		return
	try:
		removed_uids = Achievements.cleanup_mision_imposible()
	except Exception as e:
		bot.send_message(uid, "Error al correr la limpieza: %s" % str(e))
		return
	if removed_uids:
		texto = "🧹 Se quitó *Misión Imposible* a {} jugador{} que no cumplían la regla correcta.".format(
			len(removed_uids), "" if len(removed_uids) == 1 else "es")
	else:
		texto = "🧹 No había nadie con el logro mal otorgado."
	bot.edit_message_text(texto, chat_id=callback.message.chat_id, message_id=callback.message.message_id,
		parse_mode=ParseMode.MARKDOWN)

# help page
def command_help(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	cid = update.message.chat_id
	help_text = "Los siguientes comandos están disponibles:\n"
	for i in commands:
		help_text += i + "\n"
	bot.send_message(cid, help_text)

def command_newgame(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	cid = update.message.chat_id
	groupName = update.message.chat.title	
	try:
		game = get_game(cid)
		groupType = update.message.chat.type
		if groupType not in ['group', 'supergroup']:
			bot.send_message(cid, "Tienes que agregarme a un grupo primero y escribir /newgame allá!")
		elif game:
			bot.send_message(cid, "Hay un juego comenzado en este chat. Si quieres terminarlo escribe /cancelgame!")
		else:
			GamesController.games[cid] = Game(cid, update.message.from_user.id, groupName)
			bot.send_message(cid, "Nuevo juego creado! Cada jugador debe unirse al juego con el comando /join.\nEl iniciador del juego (o el administrador) pueden unirse tambien y escribir /startgame cuando todos se hayan unido al juego!")
			
	except Exception as e:
		bot.send_message(cid, str(e))


def command_join(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	# I use args for testing. // Remove after?
	groupName = update.message.chat.title
	cid = update.message.chat_id
	groupType = update.message.chat.type
	game = get_game(cid)
	if len(args) <= 0:
		# if not args, use normal behaviour
		fname = update.message.from_user.first_name.replace("_", " ")
		uid = update.message.from_user.id
	else:
		uid = update.message.from_user.id
		if uid == ADMIN:
			for i,k in zip(args[0::2], args[1::2]):
				fname = i.replace("_", " ")
				uid = int(k)
				player = Player(fname, uid)
				game.add_player(uid, player)
				log.info("%s (%d) joined a game in %d" % (fname, uid, game.cid))
				save_game(cid, "Game in join state", game)
	
	if groupType not in ['group', 'supergroup']:
		bot.send_message(cid, "Tienes que agregarme a un grupo primero y escribir /newgame allá!")
	elif not game:
		bot.send_message(cid, "No hay juego en este chat. Crea un nuevo juego con /newgame")
	elif game.board:
		bot.send_message(cid, "El juego ha comenzado. Por favor espera el proximo juego!")
	elif uid in game.playerlist:
		bot.send_message(game.cid, "Ya te has unido al juego, %s!" % fname)
	elif len(game.playerlist) >= 10:
		bot.send_message(game.cid, "Han llegado al maximo de jugadores. Por favor comiencen el juego con /startgame!")
	else:
		#uid = update.message.from_user.id
		player = Player(fname, uid)
		try:
			#Commented to dont disturb player during testing uncomment in production
			bot.send_message(uid, "Te has unido a un juego en %s. Pronto te dire cual es tu rol secreto." % groupName)
			choose_posible_role(bot, cid, uid)
			
			game.add_player(uid, player)
			log.info("%s (%d) joined a game in %d" % (fname, uid, game.cid))
			if len(game.playerlist) > 4:
				bot.send_message(game.cid, fname + " se ha unido al juego. Escribe /startgame si este es el último jugador y quieren comenzar con %d jugadores!" % len(game.playerlist))
			elif len(game.playerlist) == 1:
				bot.send_message(game.cid, "%s se ha unido al juego. Hay %d jugador en el juego y se necesita 5-10 jugadores." % (fname, len(game.playerlist)))
			else:
				bot.send_message(game.cid, "%s se ha unido al juego. Hay %d jugadores en el juego y se necesita 5-10 jugadores" % (fname, len(game.playerlist)))
			# Luego dicto los jugadores que se han unido
			jugadoresActuales = "Los jugadores que se han unido al momento son:\n"
			for uid in game.playerlist:
				jugadoresActuales += "%s\n" % game.playerlist[uid].name
			bot.send_message(game.cid, jugadoresActuales)
			save_game(cid, "Game in join state", game)
		except Exception as e:
			log.error(e)
			bot.send_message(game.cid,
				fname + ", No te puedo enviar un mensaje privado. Por favor, ve a @secrethitlertestlbot y has pincha \"Start\".\nLuego necesitas escribir /join de nuevo.")


def command_startgame(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	log.info('command_startgame called')
	groupName = update.message.chat.title
	cid = update.message.chat_id
	game = get_game(cid)
	if not game:
		bot.send_message(cid, "No hay juego en este chat. Crea un nuevo juego con /newgame")
	elif game.board:
		bot.send_message(cid, "El juego ya ha comenzado!")
	elif update.message.from_user.id != game.initiator and bot.getChatMember(cid, update.message.from_user.id).status not in ("administrator", "creator"):
		bot.send_message(game.cid, "Solo el creador del juego o un administrador del grupo pueden comenzar el juego con /startgame")
	elif len(game.playerlist) < 5:
		bot.send_message(game.cid, "No hay suficientes jugadores (min. 5, max. 10). Uneté al juego con /join")
	else:
		player_number = len(game.playerlist)
		MainController.inform_players(bot, game, game.cid, player_number)
		MainController.inform_fascists(bot, game, player_number)
		game.board = Board(player_number, game)
		log.info(game.board)
		log.info("len(games) Command_startgame: " + str(len(GamesController.games)))
		game.shuffle_player_sequence()
		game.board.state.player_counter = 0
		#print_board(bot, game, cid)
		#group_name = update.message.chat.title
		#bot.send_message(ADMIN, "Game of Secret Hitler started in group %s (%d)" % (group_name, cid))		
		MainController.start_round(bot, game)
		#save_game(cid, groupName, game)

def command_cancelgame(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('command_cancelgame called')
	cid = update.message.chat_id
	uid = update.message.from_user.id
	#Always try to delete in DB

	game = get_game(cid)

	#delete_game(cid)
	if game:
		status = bot.getChatMember(cid, uid).status
		if uid == game.initiator or status in ("administrator", "creator"):
			btns = [[InlineKeyboardButton("Sí, cancelar el juego", callback_data="{}*confirmCancel*si*{}".format(cid, uid)),
					InlineKeyboardButton("No", callback_data="{}*confirmCancel*no*{}".format(cid, uid))]]
			bot.send_message(cid, "¿Estás seguro de que quieres cancelar el juego? Todos los datos del juego serán borrados.", reply_markup=InlineKeyboardMarkup(btns))
		else:
			bot.send_message(cid, "Solo el creador del juego o el administrador del grupo pueden cancelar el juego con /cancelgame")
	else:
		bot.send_message(cid, "No hay juego en este chat. Crea un nuevo juego con /newgame")

def callback_cancelgame_confirm(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_cancelgame_confirm called')
	callback = update.callback_query

	regex = re.search(r"(-?[0-9]*)\*confirmCancel\*(si|no)\*(-?[0-9]*)", callback.data)
	cid, opcion, uid = int(regex.group(1)), regex.group(2), int(regex.group(3))

	if callback.from_user.id != uid:
		callback.answer("Solo quien ejecutó /cancelgame puede confirmar.")
		return

	if opcion == "si":
		game = get_game(cid)
		if game:
			bot.edit_message_text("Juego cancelado.", cid, callback.message.message_id)
			MainController.end_game(bot, game, 99)
		else:
			bot.edit_message_text("No hay juego en este chat. Crea un nuevo juego con /newgame", cid, callback.message.message_id)
	else:
		bot.edit_message_text("Cancelación abortada, el juego continúa.", cid, callback.message.message_id)

def command_votes(update: Update, context: CallbackContext):
	bot = context.bot
	try:
		#Send message of executing command   
		cid = update.message.chat_id
		#bot.send_message(cid, "Looking for history...")
		#Check if there is a current game 
		game = get_game(cid)
		if game:			
			if not game.dateinitvote:
				# If date of init vote is null, then the voting didnt start          
				bot.send_message(cid, "La votación no ha comenzado todavia!")
			else:
				#If there is a time, compare it and send history of votes.
				start = game.dateinitvote
				stop = datetime.datetime.now()
				elapsed = stop - start
				if elapsed > datetime.timedelta(minutes=5):
					history_text = "Historial de votacion para el Presidente %s y Canciller %s:\n\n" % (game.board.state.nominated_president.name, game.board.state.nominated_chancellor.name)
					for player in game.player_sequence:
						# If the player is in the last_votes (He voted), mark him as he registered a vote
						if player.uid in game.board.state.last_votes:
							history_text += "%s ha votado.\n" % (game.playerlist[player.uid].name)
						else:
							history_text += "%s *no* ha votado.\n" % (game.playerlist[player.uid].name)
					bot.send_message(cid, history_text, ParseMode.MARKDOWN)
				else:
					bot.send_message(cid, "Cinco minutos deben pasar para ver los votos") 
		else:
			bot.send_message(cid, "No hay juego en este chat. Crea un nuevo juego con /newgame")
	except Exception as e:
		bot.send_message(cid, str(e))

def command_calltovote(update: Update, context: CallbackContext):
	bot = context.bot
	try:
		#Send message of executing command
		cid = update.message.chat_id
		#bot.send_message(cid, "Looking for history...")
		#Check if there is a current game
		game = get_game(cid)
		if game:
			if game.board is not None and _game_has_ended(game):
				# La partida ya termino y esta esperando los votos de /mvp.
				faltan = [p for u, p in game.playerlist.items() if u not in getattr(game, "mvp_votes", {})]
				if not faltan:
					bot.send_message(cid, "¡Ya votaron todos! El resultado del MVP se revela en breve.")
				else:
					texto = "🏅 Todavía falta que voten quién fue el MVP de la partida:\n"
					for p in faltan:
						texto += "[%s](tg://user?id=%d) - ¡Usá /mvp en privado!\n" % (p.name, p.uid)
					bot.send_message(cid, texto, parse_mode=ParseMode.MARKDOWN)
				return
			if not game.dateinitvote:
				# If date of init vote is null, then the voting didnt start
				bot.send_message(cid, "La votación no ha comenzado todavia!")
			else:
				#If there is a time, compare it and send history of votes.
				strcid = str(game.cid)
				btns = [[InlineKeyboardButton("Ja", callback_data=strcid + "_Ja"),
				InlineKeyboardButton("Nein", callback_data=strcid + "_Nein")]]
				voteMarkup = InlineKeyboardMarkup(btns)
				
				start = game.dateinitvote
				stop = datetime.datetime.now()          
				elapsed = stop - start
				if elapsed > datetime.timedelta(minutes=1):
					# Only remember to vote to players that are still in the game
					history_text = ""
					for player in game.player_sequence:
						# If the player is not in last_votes send him reminder
						if player.uid not in game.board.state.last_votes:
							history_text += "Es hora de votar [%s](tg://user?id=%d)!\n" % (game.playerlist[player.uid].name, player.uid)
							groupName = "*En el grupo {}*\n".format(game.groupName)
							msg = "{}Quieres elegir al Presidente *{}* y al canciller *{}*?".format(groupName, game.board.state.nominated_president.name, game.board.state.nominated_chancellor.name)
							bot.send_message(player.uid, msg, reply_markup=voteMarkup, parse_mode=ParseMode.MARKDOWN)
					bot.send_message(cid, text=history_text, parse_mode=ParseMode.MARKDOWN)
				else:
					bot.send_message(cid, "Cinco minutos deben pasar para pedir que se vote!") 
		else:
			bot.send_message(cid, "No hay juego en este chat. Crea un nuevo juego con /newgame")
	except Exception as e:
		bot.send_message(cid, str(e))

def retract_player_vote(bot, game, uid):
	# Realiza el retiro del voto del jugador y avisa en qué grupo se retiró
	del game.board.state.last_votes[uid]
	save_game(game.cid, "retract vote Round %d" % (game.board.state.currentround), game)
	nombre = game.playerlist[uid].name
	grupo = game.groupName if (hasattr(game, 'groupName') and game.groupName) else str(game.cid)
	# Aviso en el grupo para que el resto de jugadores lo vea
	bot.send_message(game.cid, "%s ha retirado su voto." % nombre)
	# Le mando al jugador la confirmación (indicando el grupo) y botones para volver a votar
	strcid = str(game.cid)
	btns = [[InlineKeyboardButton("Ja", callback_data=strcid + "_Ja"),
	InlineKeyboardButton("Nein", callback_data=strcid + "_Nein")]]
	voteMarkup = InlineKeyboardMarkup(btns)
	msg = "Has retirado tu voto en el grupo *{}*. Puedes volver a votar aquí.\nQuieres elegir al Presidente *{}* y al canciller *{}*?".format(grupo, game.board.state.nominated_president.name, game.board.state.nominated_chancellor.name)
	try:
		bot.send_message(uid, msg, reply_markup=voteMarkup, parse_mode=ParseMode.MARKDOWN)
	except Exception as e:
		log.error(str(e))

def command_retract_vote(update: Update, context: CallbackContext):
	bot = context.bot
	try:
		#Retira el voto de Ja o Nein del jugador que ejecuta el comando
		cid, uid, groupType = update.message.chat_id, update.message.from_user.id, update.message.chat.type
		if groupType not in ['group', 'supergroup']:
			# En privado con el bot: busco los juegos donde el jugador tiene un voto activo para retirar
			all_games_unfiltered = MainController.getGamesByTipo("Todos") or {}
			retractable = {key: "{}: {}".format(g.groupName, g.tipo) for key, g in all_games_unfiltered.items()
				if uid in g.playerlist and g.board is not None and g.dateinitvote and uid in g.board.state.last_votes}
			if not retractable:
				bot.send_message(uid, "No tienes ningún voto activo que retirar.")
			elif len(retractable) == 1:
				game = get_game(int(list(retractable.keys())[0]))
				retract_player_vote(bot, game, uid)
			else:
				msg = "Elija el grupo del cual quiere retirar su voto"
				simple_choose_buttons(bot, cid, uid, uid, "chooseGameRetract", msg, retractable)
		else:
			#Check if there is a current game
			game = get_game(cid)
			if game:
				if not game.dateinitvote:
					# If date of init vote is null, then the voting didnt start
					bot.send_message(cid, "La votación no ha comenzado todavia!")
				elif uid not in game.playerlist:
					bot.send_message(cid, "No estás en este juego!")
				elif uid not in game.board.state.last_votes:
					bot.send_message(cid, "No has votado todavia, no hay voto que retirar!")
				else:
					retract_player_vote(bot, game, uid)
			else:
				bot.send_message(cid, "No hay juego en este chat. Crea un nuevo juego con /newgame")
	except Exception as e:
		bot.send_message(update.message.chat_id, str(e))

def callback_retract(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_retract called')
	callback = update.callback_query
	regex = re.search(r"(-?[0-9]*)\*chooseGameRetract\*(.*)\*(-?[0-9]*)", callback.data)
	opcion, uid = regex.group(2), int(regex.group(3))
	game = get_game(int(opcion))
	if not game or not game.dateinitvote:
		bot.send_message(uid, "La votación ya no está activa, no hay voto que retirar.")
	elif uid not in game.board.state.last_votes:
		bot.send_message(uid, "No tienes un voto activo que retirar en ese grupo.")
	else:
		retract_player_vote(bot, game, uid)

def set_auto_ja(bot, game, uid, enabled):
	# Activa o desactiva el voto Ja automático del jugador para este juego
	game.playerlist[uid].auto_ja = enabled
	save_game(game.cid, "auto_ja %s Round %d" % ("on" if enabled else "off", game.board.state.currentround), game)
	if enabled:
		bot.send_message(uid,
			"Voto automático *Ja* activado en *{}*. Mientras no estemos en Zona Hitler (menos de 3 políticas fascistas promulgadas), tu voto Ja se registrará solo apenas se proponga una fórmula. Usa /stopautoja para desactivarlo.".format(game.groupName),
			parse_mode=ParseMode.MARKDOWN)
		# Si hay una votación en curso y el jugador todavia no voto, le registro el Ja ahora mismo
		if game.dateinitvote and uid not in game.board.state.last_votes and not MainController.is_zona_hitler(game):
			game.board.state.last_votes[uid] = "Ja"
			save_game(game.cid, "auto_ja vote Round %d" % (game.board.state.currentround), game)
			bot.send_message(uid, "Tu voto *Ja* para la votación en curso ya quedó registrado.", parse_mode=ParseMode.MARKDOWN)
			if len(game.board.state.last_votes) == len(game.player_sequence):
				MainController.count_votes(bot, game)
	else:
		bot.send_message(uid, "Voto automático *Ja* desactivado en *{}*.".format(game.groupName), parse_mode=ParseMode.MARKDOWN)

def _command_toggle_auto_ja(update: Update, context: CallbackContext, enabled, comando_callback):
	bot = context.bot
	try:
		cid, uid, groupType = update.message.chat_id, update.message.from_user.id, update.message.chat.type
		if groupType not in ['group', 'supergroup']:
			# En privado con el bot: busco los juegos activos donde esta el jugador
			all_games_unfiltered = MainController.getGamesByTipo("Todos") or {}
			candidatas = {key: "{}: {}".format(g.groupName, g.tipo) for key, g in all_games_unfiltered.items()
				if uid in g.playerlist and g.board is not None}
			if not candidatas:
				bot.send_message(uid, "No tienes partidas activas de Secret Hitler.")
			elif len(candidatas) == 1:
				game = get_game(int(list(candidatas.keys())[0]))
				set_auto_ja(bot, game, uid, enabled)
			else:
				msg = "Elige el juego donde quieres {} el voto automático Ja".format("activar" if enabled else "desactivar")
				simple_choose_buttons(bot, cid, uid, uid, comando_callback, msg, candidatas)
		else:
			game = get_game(cid)
			if not game or game.board is None:
				bot.send_message(cid, "No hay juego en este chat. Crea un nuevo juego con /newgame")
			elif uid not in game.playerlist:
				bot.send_message(cid, "No estás en este juego!")
			else:
				set_auto_ja(bot, game, uid, enabled)
	except Exception as e:
		bot.send_message(update.message.chat_id, str(e))

def command_startautoja(update: Update, context: CallbackContext):
	_command_toggle_auto_ja(update, context, True, "chooseGameStartAutoJa")

def command_stopautoja(update: Update, context: CallbackContext):
	_command_toggle_auto_ja(update, context, False, "chooseGameStopAutoJa")

def callback_startautoja(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_startautoja called')
	callback = update.callback_query
	regex = re.search(r"(-?[0-9]*)\*chooseGameStartAutoJa\*(.*)\*(-?[0-9]*)", callback.data)
	opcion, uid = regex.group(2), int(regex.group(3))
	game = get_game(int(opcion))
	if not game or uid not in game.playerlist:
		bot.send_message(uid, "No estás en ese juego.")
	else:
		set_auto_ja(bot, game, uid, True)

def callback_stopautoja(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_stopautoja called')
	callback = update.callback_query
	regex = re.search(r"(-?[0-9]*)\*chooseGameStopAutoJa\*(.*)\*(-?[0-9]*)", callback.data)
	opcion, uid = regex.group(2), int(regex.group(3))
	game = get_game(int(opcion))
	if not game or uid not in game.playerlist:
		bot.send_message(uid, "No estás en ese juego.")
	else:
		set_auto_ja(bot, game, uid, False)

def command_showhistory(update: Update, context: CallbackContext):
	bot = context.bot
	#game.pedrote = 3
	try:
		#Send message of executing command   
		cid = update.message.chat_id
		#Check if there is a current game 
		
		groupName = update.message.chat.title

		game = get_game(cid)
		if game:			
			#bot.send_message(cid, "Current round: " + str(game.board.state.currentround + 1))
			uid = update.message.from_user.id
			game.groupName = groupName
			history_text = "Historial del grupo *{}*:\n\n".format(groupName)
			history_textContinue = "" 
			for x in game.history:
				if len(history_text) < 3500:
					history_text += x + "\n\n"
				else:
					history_textContinue += x + "\n\n"

			bot.send_message(uid, history_text, ParseMode.MARKDOWN)
			if len(history_textContinue) > 0:
				bot.send_message(uid, history_textContinue, ParseMode.MARKDOWN)
			#bot.send_message(cid, "I sent you the history to our private chat")			
		else:
			bot.send_message(cid, "No hay juego en este chat. Crea un nuevo juego con /newgame")
	except Exception as e:
		bot.send_message(cid, str(e))
		log.error("Unknown error: " + str(e))  
		
def command_claim(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	#game.pedrote = 3
	try:
		#Send message of executing command   
		cid = update.message.chat_id
		#Check if there is a current game 
		game = get_game(cid)
		if game:
			uid = update.message.from_user.id
			if uid in game.playerlist:				
				if (game.board.state.liberal_track + game.board.state.fascist_track) > 0:
					if len(args) > 0:
						#Data is being claimed
						claimtext = ' '.join(args)
						claimtexttohistory = "El jugador %s declara: %s" % (game.playerlist[uid].name, claimtext)
						bot.send_message(cid, "Tu declaración: %s fue agregada al historial." % (claimtext))
						game.history.append("%s" % (claimtexttohistory))
						save_game(cid, "Game in join state", game)
					else:					
						bot.send_message(cid, "Debes mandar un mensaje para hacer una declaración.")

				else:
					bot.send_message(cid, "No puedes hacer sin promulgar al menos una política.")
			else:
				bot.send_message(cid, "Debes ser un jugador del partido para declarar algo.")
				
		else:
			bot.send_message(cid, "No hay juego en este chat. Crea un nuevo juego con /newgame")
	except Exception as e:
		bot.send_message(cid, str(e))
		log.error("Unknown error: " + str(e))    

		
def command_claim_oculto(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	try:
		#Send message of executing command   
		cid = update.message.chat_id
		uid = update.message.from_user.id
		
		# Busco en que juegos esta el jugador y agrego el historia oculto en los que este. (Futuro se
		for game_key, game in GamesController.games.items():
			#Solamente si el jugador esta en el partido y 
			if uid in game.playerlist:
				#Check if there is a current game
				if (game.board.state.liberal_track + game.board.state.fascist_track) > 0:
					if len(args) > 0:
						#Data is being claimed
						claimtext = ' '.join(args)
						claimtexttohistory = "El jugador %s declara: %s" % (game.playerlist[uid].name, claimtext)
						bot.send_message(uid, "Tu declaración: %s fue agregada al historial oculto." % (claimtext))
						game.hiddenhistory.append("%s" % (claimtexttohistory))
					else:					
						bot.send_message(uid, "Debes mandar un mensaje para hacer una declaración.")

				else:
					bot.send_message(uid, "No puedes hacer claim oculto sin promulgar al menos una política.")
			else:
				bot.send_message(uid, "No puedes hacer claim oculto si no estas en algun partido.")				
	except Exception as e:
		bot.send_message(uid, str(e))
		log.error("Unknown error: " + str(e))
		
def save_game(cid, groupName, game):
	#Check if game is in DB first
	conn = psycopg2.connect(
		database=url.path[1:],
		user=url.username,
		password=url.password,
		host=url.hostname,
		port=url.port
	)
	cur = conn.cursor()			
	log.info("Searching Game in DB")
	query = "select * from games_secret_hitler where id = %s;"
	cur.execute(query, [cid])
	dbdata = cur.fetchone()
	if cur.rowcount > 0:
		log.info('Updating Game')
		gamejson = jsonpickle.encode(game)
		#query = "UPDATE games_secret_hitler SET groupName = %s, data = %s WHERE id = %s RETURNING data;"
		query = "UPDATE games_secret_hitler SET groupName = %s, data = %s WHERE id = %s;"
		cur.execute(query, (groupName, gamejson, cid))
		#log.info(cur.fetchone()[0])
		conn.commit()		
	else:
		log.info('Saving Game in DB')
		gamejson = jsonpickle.encode(game)
		query = "INSERT INTO games_secret_hitler(id , groupName  , data) VALUES (%s, %s, %s);"
		#query = "INSERT INTO games(id , groupName  , data) VALUES (%s, %s, %s) RETURNING data;"
		cur.execute(query, (cid, groupName, gamejson))
		#log.info(cur.fetchone()[0])
		conn.commit()
	conn.close()

def load_game(cid):
	conn = psycopg2.connect(
				database=url.path[1:],
				user=url.username,
				password=url.password,
				host=url.hostname,
				port=url.port
			)
	cur = conn.cursor()			
	log.info("Searching Game in DB")
	query = "SELECT * FROM games_secret_hitler WHERE id = %s;"
	cur.execute(query, [cid])
	dbdata = cur.fetchone()

	if cur.rowcount > 0:
		log.info("Game Found")
		jsdata = dbdata[2]
		#log.info("jsdata = %s" % (jsdata))				
		game = jsonpickle.decode(jsdata)
		
		# For some reason the decoding fails when bringing the dict playerlist and it changes it id from int to string.
		# So I have to change it back the ID to int.				
		temp_player_list = {}
		for uid in game.playerlist:
			temp_player_list[int(uid)] = game.playerlist[uid]
		game.playerlist = temp_player_list

		# Partidas guardadas antes de agregar /guess no tienen este atributo.
		if not hasattr(game, "guesses"):
			game.guesses = {}
		temp_guesses = {}
		for guesser_uid in game.guesses:
			history = game.guesses[guesser_uid]
			for entry in history:
				if "fascists" in entry:
					entry["fascists"] = [int(u) for u in entry.get("fascists", [])]
				if entry.get("hitler") is not None:
					entry["hitler"] = int(entry["hitler"])
				if entry.get("predicted") is not None:
					entry["predicted"] = int(entry["predicted"])
			temp_guesses[int(guesser_uid)] = history
		game.guesses = temp_guesses

		# Partidas guardadas antes de agregar /mvp no tienen este atributo.
		if not hasattr(game, "mvp_votes"):
			game.mvp_votes = {}
		temp_mvp_votes = {}
		for voter_uid in game.mvp_votes:
			temp_mvp_votes[int(voter_uid)] = int(game.mvp_votes[voter_uid])
		game.mvp_votes = temp_mvp_votes

		if not hasattr(game, "stats_game_id"):
			game.stats_game_id = None

		if game.board is not None and game.board.state is not None:
			temp_last_votes = {}	
			for uid in game.board.state.last_votes:
				temp_last_votes[int(uid)] = game.board.state.last_votes[uid]
			game.board.state.last_votes = temp_last_votes
		#bot.send_message(cid, game.print_roles())
		conn.close()
		return game
	else:
		log.info("Game Not Found")
		conn.close()
		return None

def delete_game(cid):
	conn = psycopg2.connect(
		database=url.path[1:],
		user=url.username,
		password=url.password,
		host=url.hostname,
		port=url.port
	)
	cur = conn.cursor()
	log.info("Deleting Game in DB")
	query = "DELETE FROM games_secret_hitler WHERE id = %s;"
	cur.execute(query, [cid])
	conn.commit()
	conn.close()
	
	
#Testing commands
def command_ja(update: Update, context: CallbackContext):
	bot = context.bot
	uid = update.message.from_user.id
	if uid == ADMIN:
		cid = update.message.chat_id
		game = get_game(cid)
		answer = "Ja"
		for uid in game.playerlist:
			game.board.state.last_votes[uid] = answer
		MainController.count_votes(bot, game)
	

def command_nein(update: Update, context: CallbackContext):
	bot = context.bot	
	uid = update.message.from_user.id
	if uid == ADMIN:
		cid = update.message.chat_id
		game = get_game(cid)
		answer = "Nein"
		for uid in game.playerlist:
			game.board.state.last_votes[uid] = answer
		MainController.count_votes(bot, game)
		
def command_reloadgame(update: Update, context: CallbackContext):
	bot = context.bot  
	cid = update.message.chat_id
	
	try:
		game = GamesController.games.get(cid, None)
		groupType = update.message.chat.type
		if groupType not in ['group', 'supergroup']:
			bot.send_message(cid, "Tienes que agregarme a un grupo primero y escribir /reloadgame allá!")		
		else:			
			#Search game in DB
			game = load_game(cid)			
			if game:
				GamesController.games[cid] = game
				bot.send_message(cid, "Hay un juego comenzado en este chat. Si quieres terminarlo escribe /cancelgame!")				
				
				if not game.board:
					return
				
				# Ask the president to choose a chancellor								
				if game.board.state.nominated_chancellor:
					if len(game.board.state.last_votes) == len(game.player_sequence):
						print_board(bot, game, cid)
						MainController.count_votes(bot, game)
					else:
						print_board(bot, game, cid)
						MainController.vote(bot, game)
						bot.send_message(cid, "Hay una votación en progreso utiliza /calltovote para decirles a los otros jugadores. ")
				else:
					MainController.start_round(bot, game)
			else:				
				bot.send_message(cid, "No hay juego que recargar! Crea un nuevo juego con /newgame!")
			
			
	except Exception as e:
		bot.send_message(cid, str(e))
	
def command_anarquia(update: Update, context: CallbackContext):
	bot = context.bot	
	try:
		#Send message of executing command   
		cid = update.message.chat_id
		#Check if there is a current game 
		game = get_game(cid)
		
		if game:
			uid = update.message.from_user.id
			if uid in game.playerlist:
				# Se pregunta a los jugadores si irian a anarquia,
				# esto se hace para no tener que estar pasando 3 formular y esperar que todos voten
				# SI, mitad + 1 de jugadores decide ir por anarquia.
				# Se hace y se indica quienes quisieron ir a anarquia				
				MainController.decide_anarquia(bot, game)
			else:
				bot.send_message(cid, "Debes ser un jugador del partido para preguntar por anarquia.")

		else:
			bot.send_message(cid, "No hay juego en este chat. Crea un nuevo juego con /newgame")
	except Exception as e:
		bot.send_message(cid, str(e))
		log.error("Unknown error: " + str(e))    
		
def command_fix(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	uid = update.message.from_user.id
	cid = update.message.chat_id
	groupType = update.message.chat.type
	log.info("Ingreso en FIX")
	if uid != ADMIN:
		return

	if not args:
		bot.send_message(cid, "Uso: /fix <3 letras> (F=Fascista, L=Liberal)\nEjemplo: /fix FFL")
		return

	letters = "".join(args).upper()

	if len(letters) != 3 or not all(c in "FL" for c in letters):
		bot.send_message(cid, "Debes ingresar exactamente 3 letras usando solo F (Fascista) o L (Liberal).\nEjemplo: /fix FFL")
		return

	if groupType in ['group', 'supergroup']:
		game = get_game(cid)
		if game is None or game.board is None:
			bot.send_message(cid, "No hay una partida activa en este chat.")
			return
		_apply_fix(bot, game, letters, cid)
	else:
		all_games_unfiltered = MainController.getGamesByTipo("Todos")
		all_games = {
			f"{key}_{letters}": "{}: {}".format(game.groupName, game.tipo)
			for key, game in all_games_unfiltered.items()
			if uid in game.playerlist and game.board is not None
		}
		if not all_games:
			bot.send_message(cid, "No tienes partidas activas de Secret Hitler.")
			return
		if len(all_games) == 1:
			key = next(iter(all_games))
			game_cid = int(key.rsplit("_", 1)[0])
			game = get_game(game_cid)
			_apply_fix(bot, game, letters, uid)
		else:
			msg = "Elige el juego donde quieres agregar las cartas"
			simple_choose_buttons(bot, cid, uid, uid, "chooseGameFix", msg, all_games)

def _apply_fix(bot, game, letters, notify_cid):
	card_map = {"F": "fascista", "L": "liberal"}
	new_cards = [card_map[c] for c in letters]
	game.board.policies = new_cards + game.board.policies
	save_game(game.cid, game.groupName, game)
	cards_text = ", ".join(new_cards)
	bot.send_message(notify_cid, f"Se agregaron al inicio del mazo: {cards_text}\nCartas totales en el mazo: {len(game.board.policies)}")

def callback_fix(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_fix called')
	callback = update.callback_query
	regex = re.search(r"(-?[0-9]*)\*chooseGameFix\*(.*)\*(-?[0-9]*)", callback.data)
	opcion_raw = regex.group(2)
	uid = int(regex.group(3))
	game_cid_str, letters = opcion_raw.rsplit("_", 1)
	game_cid = int(game_cid_str)
	game = get_game(game_cid)
	if game is None or game.board is None:
		bot.send_message(uid, "No hay una partida activa en ese chat.")
		return
	_apply_fix(bot, game, letters, uid)

def command_fix2(update: Update, context: CallbackContext):
	bot = context.bot
	uid = update.message.from_user.id
	cid = update.message.chat_id
	groupType = update.message.chat.type
	log.info("Ingreso en FIX2")
	if uid != ADMIN:
		return

	if groupType in ['group', 'supergroup']:
		game = get_game(cid)
		if game is None or game.board is None:
			bot.send_message(cid, "No hay una partida activa en este chat.")
			return
		_send_fix2_buttons(bot, game, uid)
	else:
		all_games_unfiltered = MainController.getGamesByTipo("Todos")
		all_games = {
			key: "{}: {}".format(game.groupName, game.tipo)
			for key, game in all_games_unfiltered.items()
			if uid in game.playerlist and game.board is not None
		}
		if not all_games:
			bot.send_message(cid, "No tienes partidas activas de Secret Hitler.")
			return
		if len(all_games) == 1:
			game_cid = int(next(iter(all_games)))
			game = get_game(game_cid)
			_send_fix2_buttons(bot, game, uid)
		else:
			msg = "Elige el juego donde quieres cambiar el canciller"
			simple_choose_buttons(bot, cid, uid, uid, "chooseGameFix2", msg, all_games)

def _send_fix2_buttons(bot, game, notify_uid):
	strcid = str(game.cid)
	btns = []
	for player_uid, player in game.playerlist.items():
		if not player.is_dead:
			btns.append([InlineKeyboardButton(player.name, callback_data=strcid + "_fix2chan_" + str(player_uid))])
	if not btns:
		bot.send_message(notify_uid, "No hay jugadores vivos en esta partida.")
		return
	markup = InlineKeyboardMarkup(btns)
	bot.send_message(notify_uid, "Elige quién será el canciller (sin restricciones):", reply_markup=markup)

def callback_fix2_game(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_fix2_game called')
	callback = update.callback_query
	regex = re.search(r"(-?[0-9]*)\*chooseGameFix2\*(.*)\*(-?[0-9]*)", callback.data)
	game_cid = int(regex.group(2))
	uid = int(regex.group(3))
	game = get_game(game_cid)
	if game is None or game.board is None:
		bot.send_message(uid, "No hay una partida activa en ese chat.")
		return
	_send_fix2_buttons(bot, game, uid)

def callback_fix2_chancellor(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_fix2_chancellor called')
	callback = update.callback_query
	regex = re.search(r"(-?[0-9]*)_fix2chan_(.*)", callback.data)
	cid = int(regex.group(1))
	chosen_uid = int(regex.group(2))
	game = get_game(cid)
	if game is None or game.board is None:
		bot.send_message(callback.from_user.id, "No hay una partida activa.")
		return
	player = game.playerlist.get(chosen_uid)
	if player is None:
		bot.send_message(callback.from_user.id, "Jugador no encontrado.")
		return
	# Garantizar que nominated_president esté seteado para la fase de votación
	if game.board.state.nominated_president is None:
		game.board.state.nominated_president = game.board.state.president
	if game.board.state.nominated_president is None:
		for p in (game.board.state.president, *game.player_sequence):
			if p is not None and not p.is_dead:
				game.board.state.nominated_president = p
				break
	game.board.state.nominated_chancellor = player
	bot.edit_message_text(
		f"Nominaste a {player.name} como canciller!",
		callback.from_user.id, callback.message.message_id)
	bot.send_message(game.cid,
		"Se nominó a *{}* como canciller. ¡Por favor, voten ahora!".format(player.name),
		parse_mode=ParseMode.MARKDOWN)
	# Se setea la fase y se guarda antes de votar, porque vote() puede
	# terminar la votación en el momento si todos los votos ya estan
	# registrados por /startautoja, y eso avanza la ronda a otra fase.
	game.board.state.fase = "vote"
	save_game(game.cid, "vote Round %d" % game.board.state.currentround, game)
	MainController.vote(bot, game)

def command_fix3(update: Update, context: CallbackContext):
	bot = context.bot
	uid = update.message.from_user.id
	cid = update.message.chat_id
	groupType = update.message.chat.type
	log.info("Ingreso en FIX3")
	if uid != ADMIN:
		return

	if groupType in ['group', 'supergroup']:
		game = get_game(cid)
		if game is None or game.board is None:
			bot.send_message(cid, "No hay una partida activa en este chat.")
			return
		_apply_fix3(bot, game, uid)
	else:
		all_games_unfiltered = MainController.getGamesByTipo("Todos")
		all_games = {
			key: "{}: {}".format(game.groupName, game.tipo)
			for key, game in all_games_unfiltered.items()
			if uid in game.playerlist and game.board is not None
		}
		if not all_games:
			bot.send_message(cid, "No tienes partidas activas de Secret Hitler.")
			return
		if len(all_games) == 1:
			game_cid = int(next(iter(all_games)))
			game = get_game(game_cid)
			_apply_fix3(bot, game, uid)
		else:
			msg = "Elige el juego donde quieres arreglar las cartas"
			simple_choose_buttons(bot, cid, uid, uid, "chooseGameFix3", msg, all_games)

def callback_fix3_game(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_fix3_game called')
	callback = update.callback_query
	regex = re.search(r"(-?[0-9]*)\*chooseGameFix3\*(.*)\*(-?[0-9]*)", callback.data)
	game_cid = int(regex.group(2))
	uid = int(regex.group(3))
	game = get_game(game_cid)
	if game is None or game.board is None:
		bot.send_message(uid, "No hay una partida activa en ese chat.")
		return
	_apply_fix3(bot, game, uid)

def _apply_fix3(bot, game, notify_uid):
	drawn = game.board.state.drawn_policies
	if len(drawn) <= 3:
		bot.send_message(notify_uid, "Las cartas ya están bien ({} cartas en drawn_policies).".format(len(drawn)))
		return
	removed = drawn[3:]
	game.board.state.drawn_policies = drawn[:3]
	game.board.discards.extend(removed)
	strcid = str(game.cid)
	btns = []
	for policy in game.board.state.drawn_policies:
		btns.append([InlineKeyboardButton(policy, callback_data=strcid + "_" + policy)])
	markup = InlineKeyboardMarkup(btns)
	bot.send_message(notify_uid, "Se eliminaron {} cartas extra. Cartas restantes: {}".format(
		len(removed), ", ".join(game.board.state.drawn_policies)))
	president_uid = game.board.state.president.uid if game.board.state.president else None
	if president_uid and not game.is_debugging:
		bot.send_message(president_uid,
			"Cartas corregidas. Por favor elige cuál descartar:",
			reply_markup=markup)
	else:
		bot.send_message(notify_uid,
			"Cartas corregidas. El presidente debe elegir cuál descartar:",
			reply_markup=markup)
	game.board.state.fase = "legislating president discard"
	save_game(game.cid, "fix3 Round %d" % game.board.state.currentround, game)

def command_fix4(update: Update, context: CallbackContext):
	bot = context.bot
	uid = update.message.from_user.id
	cid = update.message.chat_id
	groupType = update.message.chat.type
	log.info("Ingreso en FIX4")
	if uid != ADMIN:
		return

	if groupType in ['group', 'supergroup']:
		game = get_game(cid)
		if game is None or game.board is None:
			bot.send_message(cid, "No hay una partida activa en este chat.")
			return
		_apply_fix4(bot, game, cid)
	else:
		all_games_unfiltered = MainController.getGamesByTipo("Todos")
		all_games = {
			key: "{}: {}".format(game.groupName, game.tipo)
			for key, game in all_games_unfiltered.items()
			if uid in game.playerlist and game.board is not None
		}
		if not all_games:
			bot.send_message(cid, "No tienes partidas activas de Secret Hitler.")
			return
		if len(all_games) == 1:
			game_cid = int(next(iter(all_games)))
			game = get_game(game_cid)
			_apply_fix4(bot, game, uid)
		else:
			msg = "Elige el juego donde quieres resetear el mazo"
			simple_choose_buttons(bot, cid, uid, uid, "chooseGameFix4", msg, all_games)

def callback_fix4_game(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_fix4_game called')
	callback = update.callback_query
	regex = re.search(r"(-?[0-9]*)\*chooseGameFix4\*(.*)\*(-?[0-9]*)", callback.data)
	game_cid = int(regex.group(2))
	uid = int(regex.group(3))
	game = get_game(game_cid)
	if game is None or game.board is None:
		bot.send_message(uid, "No hay una partida activa en ese chat.")
		return
	_apply_fix4(bot, game, uid)

def _apply_fix4(bot, game, notify_cid):
	new_deck = ["liberal"] * 4 + ["fascista"] * 8
	random.shuffle(new_deck)
	game.board.policies = new_deck
	save_game(game.cid, "fix4 Round %d" % game.board.state.currentround, game)
	bot.send_message(notify_cid, "Mazo reseteado: 4 liberales y 8 fascistas mezclados.\nCartas totales en el mazo: {}".format(len(game.board.policies)))

def command_fix5(update: Update, context: CallbackContext):
	bot = context.bot
	uid = update.message.from_user.id
	cid = update.message.chat_id
	groupType = update.message.chat.type
	log.info("Ingreso en FIX5")
	if uid != ADMIN:
		return

	if groupType in ['group', 'supergroup']:
		game = get_game(cid)
		if game is None or game.board is None:
			bot.send_message(cid, "No hay una partida activa en este chat.")
			return
		_apply_fix5(bot, game, cid)
	else:
		all_games_unfiltered = MainController.getGamesByTipo("Todos")
		all_games = {
			key: "{}: {}".format(game.groupName, game.tipo)
			for key, game in all_games_unfiltered.items()
			if uid in game.playerlist and game.board is not None
		}
		if not all_games:
			bot.send_message(cid, "No tienes partidas activas de Secret Hitler.")
			return
		if len(all_games) == 1:
			game_cid = int(next(iter(all_games)))
			game = get_game(game_cid)
			_apply_fix5(bot, game, uid)
		else:
			msg = "Elige el juego donde quieres reenviar el menú de investigación"
			simple_choose_buttons(bot, cid, uid, uid, "chooseGameFix5", msg, all_games)

def callback_fix5_game(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_fix5_game called')
	callback = update.callback_query
	regex = re.search(r"(-?[0-9]*)\*chooseGameFix5\*(.*)\*(-?[0-9]*)", callback.data)
	game_cid = int(regex.group(2))
	uid = int(regex.group(3))
	game = get_game(game_cid)
	if game is None or game.board is None:
		bot.send_message(uid, "No hay una partida activa en ese chat.")
		return
	_apply_fix5(bot, game, uid)

def _apply_fix5(bot, game, notify_cid):
	if game.board.state.president is None:
		bot.send_message(notify_cid, "No hay un Presidente actual en esta partida.")
		return
	# Reafirmo la fase por si quedó desincronizada, y reenvío el menú al Presidente
	game.board.state.fase = "legislating power inspect"
	save_game(game.cid, "fix5 Round %d" % game.board.state.currentround, game)
	MainController.action_inspect(bot, game)
	bot.send_message(notify_cid, "Se reenvió el menú de investigación al Presidente {}.".format(game.board.state.president.name))

def command_player_counter(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	uid = update.message.from_user.id
	log.info("Ingreso en FIX")
	if uid == ADMIN:
		cid = update.message.chat_id
		game = get_game(cid)
		game.board.state.player_counter = args[0]	
		save_game(cid, "Game conflict state", game)

def command_toggle_debugging(update: Update, context: CallbackContext):
	bot = context.bot
	uid = update.message.from_user.id
	if uid == ADMIN:
		cid = update.message.chat_id
		game = get_game(cid)
		# Informo que el modo de debugging ha cambiado
		game.is_debugging = True if not game.is_debugging else False
		bot.send_message(cid, "Debug Mode: ON" if game.is_debugging else "Debug Mode: OFF")

def command_jugadores(update: Update, context: CallbackContext):
	bot = context.bot	
	uid = update.message.from_user.id
	cid = update.message.chat_id
	
	game = get_game(cid)
	jugadoresActuales = "Los jugadores que se han unido al momento son:\n"
	for uid in game.playerlist:
		jugadoresActuales += "[%s](tg://user?id=%d)\n" % (game.playerlist[uid].name, uid)
					
	bot.send_message(game.cid, jugadoresActuales, ParseMode.MARKDOWN)	
		
def command_newgame_sql_command(update: Update, context: CallbackContext):
	conn = psycopg2.connect(
		database=url.path[1:],
		user=url.username,
		password=url.password,
		host=url.hostname,
		port=url.port
	)
	bot = context.bot
	args = context.args
	cid, uid = update.message.chat_id, update.message.from_user.id
	if uid == ADMIN:
		try:
			#Check if game is in DB first
			cursor = conn.cursor()			
			log.info("Executing in DB")
			#query = "select * from games;"
			query = " ".join(args).replace('\'s', '')
			
			cursor.execute(sql.SQL(query))
			#dbdata = cur.fetchone()
			
			if 'update' in args or 'insert' in args or 'UPDATE' in args or 'INSERT' in args or 'delete' in args or 'DELETE' in args:
				conn.commit()				
				bot.send_message(cid, 'Consulta commiteada')
			else:
					
				if cursor.rowcount > 0:
					bot.send_message(cid, 'Resultado de la consulta:')
					for table in cursor.fetchall():
						#bot.send_message(cid, len(str(table)))
						tabla_str = str(table)
						# Si supera el maximo de caracteres lo parto
						if len(tabla_str) < 4096:
							bot.send_message(cid, table)
						else:
							n = 4090
							parts = [tabla_str[i:i+n] for i in range(0, len(tabla_str), n)]
							for part in parts:
								bot.send_message(cid, part)
				else:
					bot.send_message(cid, 'No se obtuvo nada de la consulta')
			conn.close()
		except Exception as e:
			bot.send_message(cid, 'No se ejecuto el comando debido a: '+str(e))
			conn.rollback()
			conn.close()

def command_choose_posible_role(update: Update, context: CallbackContext):
	bot = context.bot
	cid, uid = update.message.chat_id, update.message.from_user.id
	choose_posible_role(bot, cid, uid)
	
def choose_posible_role(bot, cid, uid):
	frase_regex = "chooserole"
	pregunta_arriba_botones = "¿Qué rol quisieras ser?"
	chat_donde_se_pregunta = uid
	multipurpose_choose_buttons(bot, cid, uid, chat_donde_se_pregunta, frase_regex, pregunta_arriba_botones, opciones_choose_posible_role)

def callback_choose_posible_role(update: Update, context: CallbackContext):
	bot = context.bot
	callback = update.callback_query
	log.info('callback_choose_posible_role called: %s' % callback.data)	
	regex = re.search("(-[0-9]*)\*chooserole\*(.*)\*([0-9]*)", callback.data)
	cid, strcid, opcion, uid, struid = int(regex.group(1)), regex.group(1), regex.group(2), int(regex.group(3)), regex.group(3)
	
	# Busco el juego actual y le pongo al jugador su preferencia, solamente si el juego no empezo hago el seteo de preferencia
	#bot.edit_message_text("Mensaje Editado: Has elegido el Rol: %s" % opcion, cid, callback.message.message_id)
	mensaje_edit = ''
	
	game = get_game(cid)
	
	if game:
		if game.board:
			mensaje_edit = 'El juego ya comenzó, intentalo cuando el juego no haya empezado'
		else:
			if uid in game.playerlist:
				mensaje_edit = 'Mensaje Editado: Has elegido el Rol: %s' % opcion
				game.playerlist[uid].preference_rol = opcion
				choose_posible_role(bot, cid, uid)
			else:
				mensaje_edit = 'No estas unido a esta partida, intentalo cuando te hayas unido'			
	else:
		mensaje_edit = 'No hay juego creado, intentalo cuando el juego este creado'		
	
	try:
		bot.edit_message_text(mensaje_edit, cid, callback.message.message_id)
	except Exception as e:
		bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)
	
	#bot.send_message(cid, "Ventana Juego: Has elegido el Rol %s" % opcion)
	#bot.send_message(uid, "Ventana Usuario: Has elegido el Rol %s" % opcion)	

def multipurpose_choose_buttons(bot, cid, uid, chat_donde_se_pregunta, comando_callback, mensaje_pregunta, opciones_botones):	
	btns = []
	# Creo los botones para elegir al usuario
	for opcion in opciones_botones:
		txtBoton = ""
		comando_op = opciones_botones[opcion]								
		for comando in comando_op["comandos"]:
			txtBoton += comando_op["comandos"][comando] + " "			
		txtBoton = txtBoton[:-1]
		datos = str(cid) + "*" + comando_callback + "*" + str(opcion) + "*" + str(uid)
		btns.append([InlineKeyboardButton(txtBoton, callback_data=datos)])
	btnMarkup = InlineKeyboardMarkup(btns)
	#for uid in game.playerlist:
	bot.send_message(chat_donde_se_pregunta, mensaje_pregunta, reply_markup=btnMarkup)

def command_info(update: Update, context: CallbackContext):
	bot = context.bot
	cid, uid, groupType = update.message.chat_id, update.message.from_user.id, update.message.chat.type
	
	if groupType not in ['group', 'supergroup']:
		# En caso de no estar en un grupo y en privado con el bot muestro todos los juegos donde esta el jugador.
		# Independeinte de si pide todos, tengo que obtenerlos a todos para preguntarle cualquier quiere tener info
		all_games_unfiltered = MainController.getGamesByTipo("Todos")	
		# Me improtan los juegos que; Este el jugador, hayan sido iniciados, datinivote no sea null y que cumpla reglas del tipo de juego en particular
		all_games = {key: "{}: {}".format(game.groupName, game.tipo) for key, game in all_games_unfiltered.items() if uid in game.playerlist and game.board != None }
		msg = "Elija el juego para obtener /info en privado"
		simple_choose_buttons(bot, cid, uid, uid, "chooseGameInfo", msg, all_games)
	else:
		groupName = update.message.chat.title
		game = get_game(cid)
		if game:
			if uid in game.playerlist:								
				player = game.playerlist[uid]
				msg = "--- *Info del grupo {}* ---\n".format(groupName)
				msg += player.get_private_info(game)
				bot.send_message(uid, msg, ParseMode.MARKDOWN)				
			else:
				bot.send_message(cid, "Debes ser un jugador del partido para obtener informacion.")
		else:
			bot.send_message(cid, "No hay juego creado en este chat")

def callback_info(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_info called')
	callback = update.callback_query
	
	regex = re.search(r"(-?[0-9]*)\*chooseGameInfo\*(.*)\*(-?[0-9]*)", callback.data)
	opcion, uid = regex.group(2), int(regex.group(3))
	
	game = get_game(int(opcion))
	
	if uid in game.playerlist:								
		player = game.playerlist[uid]
		msg = "--- *Info del grupo {}* ---\n".format(game.groupName)
		msg += player.get_private_info(game)
		bot.send_message(uid, msg, ParseMode.MARKDOWN)
	else:
		bot.send_message(uid, "Debes ser un jugador del partido para obtener informacion.")


def _guess_num_fascists(game):
	roles = playerSets.get(len(game.playerlist), {}).get("roles", [])
	return sum(1 for r in roles if r == "Fascista")

def command_guess(update: Update, context: CallbackContext):
	bot = context.bot
	uid = update.message.from_user.id
	cid = update.message.chat_id
	groupType = update.message.chat.type

	if groupType in ['group', 'supergroup']:
		game = get_game(cid)
		if game is None or game.board is None:
			bot.send_message(cid, "No hay una partida activa en este chat.")
			return
		if uid not in game.playerlist:
			bot.send_message(cid, "Debes ser un jugador de la partida para usar /guess.")
			return
		bot.send_message(cid, "Te mandé un mensaje privado para que hagas tu palpito. ¡Revisa tu chat privado conmigo!")
		_start_guess_flow(bot, game, uid)
	else:
		all_games_unfiltered = MainController.getGamesByTipo("Todos")
		all_games = {
			key: "{}: {}".format(game.groupName, game.tipo)
			for key, game in all_games_unfiltered.items()
			if uid in game.playerlist and game.board is not None
		}
		if not all_games:
			bot.send_message(cid, "No tienes partidas activas de Secret Hitler.")
			return
		if len(all_games) == 1:
			game_cid = int(next(iter(all_games)))
			game = get_game(game_cid)
			_start_guess_flow(bot, game, uid)
		else:
			msg = "Elige el juego para hacer tu palpito de quién es fascista y quién es Hitler"
			simple_choose_buttons(bot, cid, uid, uid, "chooseGameGuess", msg, all_games)

def callback_guess_game(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_guess_game called')
	callback = update.callback_query
	regex = re.search(r"(-?[0-9]*)\*chooseGameGuess\*(.*)\*(-?[0-9]*)", callback.data)
	game_cid = int(regex.group(2))
	uid = int(regex.group(3))
	game = get_game(game_cid)
	if game is None or game.board is None:
		bot.send_message(uid, "No hay una partida activa en ese chat.")
		return
	_start_guess_flow(bot, game, uid)

def _init_guess_progress(game, uid):
	# El rol determina que tiene que adivinar cada jugador:
	# - Liberal (o sin rol): adivina los fascistas comunes Y a Hitler ("full").
	# - Hitler: ya sabe que es Hitler, solo adivina a sus compañeros fascistas ("hitler").
	# - Fascista: ya sabe todo, en vez de adivinar predice quien sera el jugador que
	#   mas acierte en el modo "full" ("fascist_prediction").
	player = game.playerlist.get(uid)
	role = player.role if player else None
	if role == "Hitler":
		progress = {"mode": "hitler", "fascists": [], "num_fascists": _guess_num_fascists(game)}
	elif role == "Fascista":
		progress = {"mode": "fascist_prediction", "predicted": None}
	else:
		progress = {"mode": "full", "fascists": [], "hitler": None, "num_fascists": _guess_num_fascists(game)}
	GamesController.guess_progress[(game.cid, uid)] = progress
	return progress

def _build_first_guess_prompt(game, uid):
	progress = GamesController.guess_progress[(game.cid, uid)]
	if progress["mode"] == "fascist_prediction":
		return _build_guess_prediction_prompt(game, uid)
	return _build_guess_fascist_prompt(game, uid)

def _start_guess_flow(bot, game, uid):
	history = getattr(game, "guesses", {}).get(uid, [])
	attempts_done = len(history)
	if attempts_done >= 2:
		bot.send_message(uid, "Ya hiciste tu palpito 2 veces. Tu segunda elección quedó *definitiva* y no se puede volver a cambiar.", parse_mode=ParseMode.MARKDOWN)
		return

	player = game.playerlist.get(uid)
	role = player.role if player else None
	if role != "Fascista" and _guess_num_fascists(game) == 0:
		bot.send_message(uid, "No se puede adivinar en esta partida.")
		return

	if attempts_done == 0:
		if role == "Hitler":
			intro = ("🔮 Sos *Hitler*, así que en vez de adivinar quién es Hitler vas a intentar identificar a tus "
				"compañeros fascistas. Podés repetir esta elección una sola vez más después de confirmar; "
				"se guardan tus dos intentos, pero la *segunda* elección es la definitiva.")
		elif role == "Fascista":
			intro = ("🔮 Sos *fascista*, así que en vez de adivinar roles vas a predecir quién creés que será el "
				"jugador que más acierte a Hitler y a los fascistas comunes. Podés repetir esta elección una sola "
				"vez más después de confirmar; se guardan tus dos intentos, pero la *segunda* elección es la definitiva.")
		else:
			intro = ("🔮 Vas a elegir quiénes creés que son los fascistas comunes y quién es Hitler. "
				"Podés repetir esta elección una sola vez más después de confirmar; se guardan tus dos intentos, "
				"pero la *segunda* elección es la definitiva.")
		bot.send_message(uid, intro, parse_mode=ParseMode.MARKDOWN)
	else:
		bot.send_message(uid,
			"🔮 Esta es tu *última* oportunidad para adivinar: lo que confirmes ahora quedará definitivo.",
			parse_mode=ParseMode.MARKDOWN)

	_init_guess_progress(game, uid)
	texto, markup = _build_first_guess_prompt(game, uid)
	bot.send_message(uid, texto, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

def _build_guess_fascist_prompt(game, uid):
	progress = GamesController.guess_progress[(game.cid, uid)]
	selected = progress["fascists"]
	num_fascists = progress["num_fascists"]
	titulo = "tus compañeros fascistas" if progress["mode"] == "hitler" else "los fascistas comunes"
	texto = "🔮 *Adivina quiénes son {}* ({}/{})\n".format(titulo, len(selected), num_fascists)
	if selected:
		nombres_elegidos = ", ".join(game.playerlist[u].name for u in selected if u in game.playerlist)
		texto += "Ya elegiste: {}\n".format(nombres_elegidos)
	texto += "Elige a otro sospechoso:"
	strcid = str(game.cid)
	btns = []
	for player_uid, player in game.playerlist.items():
		if player_uid in selected:
			continue
		btns.append([InlineKeyboardButton(player.name, callback_data=strcid + "_guessf_" + str(player_uid))])
	markup = InlineKeyboardMarkup(btns)
	return texto, markup

def callback_guess_fascist(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_guess_fascist called')
	callback = update.callback_query
	regex = re.search(r"(-?[0-9]*)_guessf_(-?[0-9]*)", callback.data)
	cid = int(regex.group(1))
	candidate_uid = int(regex.group(2))
	uid = callback.from_user.id

	game = get_game(cid)
	if game is None or game.board is None:
		bot.send_message(uid, "Esa partida ya no está activa.")
		return
	if uid not in game.playerlist:
		bot.send_message(uid, "Debes ser un jugador de la partida para adivinar.")
		return

	progress = GamesController.guess_progress.get((cid, uid))
	if progress is None:
		bot.send_message(uid, "Tu sesión de /guess expiró, usa /guess de nuevo para empezar.")
		return
	if candidate_uid in game.playerlist and candidate_uid not in progress["fascists"]:
		progress["fascists"].append(candidate_uid)

	if len(progress["fascists"]) >= progress["num_fascists"]:
		if progress["mode"] == "full":
			texto, markup = _build_guess_hitler_prompt(game, uid)
		else:
			texto, markup = _build_guess_confirm_prompt(game, uid)
	else:
		texto, markup = _build_guess_fascist_prompt(game, uid)

	bot.edit_message_text(texto, chat_id=callback.message.chat_id, message_id=callback.message.message_id,
		reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

def _build_guess_hitler_prompt(game, uid):
	strcid = str(game.cid)
	texto = "🔮 *¿Quién crees que es Hitler?*"
	btns = []
	for player_uid, player in game.playerlist.items():
		btns.append([InlineKeyboardButton(player.name, callback_data=strcid + "_guessh_" + str(player_uid))])
	markup = InlineKeyboardMarkup(btns)
	return texto, markup

def callback_guess_hitler(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_guess_hitler called')
	callback = update.callback_query
	regex = re.search(r"(-?[0-9]*)_guessh_(-?[0-9]*)", callback.data)
	cid = int(regex.group(1))
	candidate_uid = int(regex.group(2))
	uid = callback.from_user.id

	game = get_game(cid)
	if game is None or game.board is None:
		bot.send_message(uid, "Esa partida ya no está activa.")
		return
	if uid not in game.playerlist:
		bot.send_message(uid, "Debes ser un jugador de la partida para adivinar.")
		return

	progress = GamesController.guess_progress.get((cid, uid))
	if progress is None:
		bot.send_message(uid, "Tu sesión de /guess expiró, usa /guess de nuevo para empezar.")
		return
	if candidate_uid in game.playerlist:
		progress["hitler"] = candidate_uid

	texto, markup = _build_guess_confirm_prompt(game, uid)
	bot.edit_message_text(texto, chat_id=callback.message.chat_id, message_id=callback.message.message_id,
		reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

def _build_guess_prediction_prompt(game, uid):
	texto = "🔮 *¿Quién creés que será el jugador que más acierte a Hitler y a los fascistas comunes?*"
	strcid = str(game.cid)
	hitler = game.get_hitler()
	excluded = {f.uid for f in game.get_fascists()}
	if hitler is not None:
		excluded.add(hitler.uid)
	btns = []
	for player_uid, player in game.playerlist.items():
		if player_uid in excluded:
			continue
		btns.append([InlineKeyboardButton(player.name, callback_data=strcid + "_guesspred_" + str(player_uid))])
	if not btns:
		for player_uid, player in game.playerlist.items():
			if player_uid == uid:
				continue
			btns.append([InlineKeyboardButton(player.name, callback_data=strcid + "_guesspred_" + str(player_uid))])
	markup = InlineKeyboardMarkup(btns)
	return texto, markup

def callback_guess_prediction(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_guess_prediction called')
	callback = update.callback_query
	regex = re.search(r"(-?[0-9]*)_guesspred_(-?[0-9]*)", callback.data)
	cid = int(regex.group(1))
	candidate_uid = int(regex.group(2))
	uid = callback.from_user.id

	game = get_game(cid)
	if game is None or game.board is None:
		bot.send_message(uid, "Esa partida ya no está activa.")
		return
	if uid not in game.playerlist:
		bot.send_message(uid, "Debes ser un jugador de la partida para adivinar.")
		return

	progress = GamesController.guess_progress.get((cid, uid))
	if progress is None:
		bot.send_message(uid, "Tu sesión de /guess expiró, usa /guess de nuevo para empezar.")
		return
	if candidate_uid in game.playerlist:
		progress["predicted"] = candidate_uid

	texto, markup = _build_guess_confirm_prompt(game, uid)
	bot.edit_message_text(texto, chat_id=callback.message.chat_id, message_id=callback.message.message_id,
		reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

def _build_guess_confirm_prompt(game, uid):
	progress = GamesController.guess_progress[(game.cid, uid)]
	strcid = str(game.cid)

	if progress["mode"] == "hitler":
		nombres_fascistas = ", ".join(game.playerlist[u].name for u in progress["fascists"] if u in game.playerlist)
		texto = "🔮 *Confirma tu palpito*\nCompañeros fascistas sospechosos: {}\n\n¿Confirmas?".format(nombres_fascistas)
	elif progress["mode"] == "fascist_prediction":
		predicted = progress.get("predicted")
		nombre = game.playerlist[predicted].name if predicted in game.playerlist else "?"
		texto = "🔮 *Confirma tu predicción*\n¿Quién más acierte a Hitler y a los fascistas?: *{}*\n\n¿Confirmas?".format(nombre)
	else:
		nombres_fascistas = ", ".join(game.playerlist[u].name for u in progress["fascists"] if u in game.playerlist)
		nombre_hitler = game.playerlist[progress["hitler"]].name if progress["hitler"] in game.playerlist else "?"
		texto = "🔮 *Confirma tu palpito*\nFascistas sospechosos: {}\nHitler: {}\n\n¿Confirmas?".format(nombres_fascistas, nombre_hitler)

	btns = [
		[InlineKeyboardButton("✅ Confirmar", callback_data=strcid + "_guessconfirm")],
		[InlineKeyboardButton("↩️ Empezar de nuevo", callback_data=strcid + "_guessrestart")],
	]
	markup = InlineKeyboardMarkup(btns)
	return texto, markup

def callback_guess_confirm(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_guess_confirm called')
	callback = update.callback_query
	regex = re.search(r"(-?[0-9]*)_guessconfirm", callback.data)
	cid = int(regex.group(1))
	uid = callback.from_user.id

	game = get_game(cid)
	if game is None or game.board is None:
		bot.send_message(uid, "Esa partida ya no está activa.")
		return
	progress = GamesController.guess_progress.get((cid, uid))
	if progress is None:
		bot.send_message(uid, "Tu sesión de /guess expiró, usa /guess de nuevo para empezar.")
		return

	if progress["mode"] == "hitler":
		entry = {"fascists": list(progress["fascists"])}
	elif progress["mode"] == "fascist_prediction":
		if progress.get("predicted") is None:
			bot.send_message(uid, "Tenés que elegir a alguien antes de confirmar.")
			return
		entry = {"predicted": progress["predicted"]}
	else:
		if progress.get("hitler") is None:
			bot.send_message(uid, "Tenés que elegir quién es Hitler antes de confirmar.")
			return
		entry = {"fascists": list(progress["fascists"]), "hitler": progress["hitler"]}

	if not hasattr(game, "guesses"):
		game.guesses = {}
	history = list(game.guesses.get(uid, []))
	history.append(entry)
	game.guesses[uid] = history
	save_game(game.cid, game.groupName, game)
	del GamesController.guess_progress[(cid, uid)]

	if len(history) >= 2:
		texto_final = ("✅ ¡Listo! Esta era tu segunda vez, así que tu palpito quedó *definitivo* y ya no se puede cambiar. "
			"Se revelará al final de la partida quién estuvo más cerca de la verdad.")
	else:
		texto_final = ("✅ ¡Listo! Tu palpito quedó guardado. Podés usar /guess una vez más para cambiarlo "
			"(la segunda vez es definitiva). Se revelará al final de la partida quién estuvo más cerca de la verdad.")

	bot.edit_message_text(texto_final, chat_id=callback.message.chat_id, message_id=callback.message.message_id,
		parse_mode=ParseMode.MARKDOWN)

def callback_guess_restart(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_guess_restart called')
	callback = update.callback_query
	regex = re.search(r"(-?[0-9]*)_guessrestart", callback.data)
	cid = int(regex.group(1))
	uid = callback.from_user.id

	game = get_game(cid)
	if game is None or game.board is None:
		bot.send_message(uid, "Esa partida ya no está activa.")
		return
	if uid not in game.playerlist:
		bot.send_message(uid, "Debes ser un jugador de la partida para adivinar.")
		return

	_init_guess_progress(game, uid)
	texto, markup = _build_first_guess_prompt(game, uid)
	bot.edit_message_text(texto, chat_id=callback.message.chat_id, message_id=callback.message.message_id,
		reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

def format_guesses_reveal(game):
	guesses = getattr(game, "guesses", {})
	if not guesses:
		return None

	hitler = game.get_hitler()
	hitler_uid = hitler.uid if hitler else None
	fascist_uids = {f.uid for f in game.get_fascists()}
	total_fascists = len(fascist_uids)

	liberal_resultados = []  # (score, name, texto) - flujo completo, arma el ranking "mas cerca de la verdad"
	hitler_lineas = []
	fascista_entries = []    # (predicted_uid, texto)

	for guesser_uid, history in guesses.items():
		if not history:
			continue
		guess = history[-1]
		guesser = game.playerlist.get(guesser_uid)
		if guesser is None:
			continue
		nota_cambio = " _(cambió su palpito una vez)_" if len(history) > 1 else ""

		if guesser.role == "Hitler":
			guessed_fascist_uids = [u for u in guess.get("fascists", []) if u in game.playerlist]
			aciertos = [u for u in guessed_fascist_uids if u in fascist_uids]
			nombres = ", ".join(game.playerlist[u].name for u in guessed_fascist_uids) or "nadie"
			hitler_lineas.append(
				"*{}* (Hitler) sospechó que sus compañeros fascistas eran: {}{}\n   ↳ Acertó {}/{} compañeros".format(
					guesser.name, nombres, nota_cambio, len(aciertos), total_fascists))
			continue

		if guesser.role == "Fascista":
			predicted_uid = guess.get("predicted")
			nombre_prediccion = game.playerlist[predicted_uid].name if predicted_uid in game.playerlist else "nadie"
			texto = "*{}* (fascista) predijo que *{}* sería quien más acierte a Hitler y a los fascistas{}".format(
				guesser.name, nombre_prediccion, nota_cambio)
			fascista_entries.append((predicted_uid, texto))
			continue

		# Liberal (o rol desconocido): flujo completo
		guessed_fascist_uids = [u for u in guess.get("fascists", []) if u in game.playerlist]
		guessed_hitler_uid = guess.get("hitler")

		aciertos_fascistas = [u for u in guessed_fascist_uids if u in fascist_uids]
		hitler_acierto = guessed_hitler_uid is not None and guessed_hitler_uid == hitler_uid
		score = len(aciertos_fascistas) + (1 if hitler_acierto else 0)

		nombres_fascistas = ", ".join(game.playerlist[u].name for u in guessed_fascist_uids) or "nadie"
		nombre_hitler = game.playerlist[guessed_hitler_uid].name if guessed_hitler_uid in game.playerlist else "nadie"

		texto = "*{}* sospechó de: {} y dijo que Hitler era *{}*{}\n   ↳ Acertó {}/{} fascistas comunes, {} a Hitler".format(
			guesser.name, nombres_fascistas, nombre_hitler, nota_cambio,
			len(aciertos_fascistas), total_fascists,
			"acertó ✅" if hitler_acierto else "no acertó ❌"
		)
		liberal_resultados.append((score, guesser.name, texto))

	if not liberal_resultados and not hitler_lineas and not fascista_entries:
		return None

	lineas = ["🔮 *Resultados de las adivinanzas* 🔮\n"]

	mejores_liberales = game.compute_best_guessers()
	if liberal_resultados:
		for _, _, texto in liberal_resultados:
			lineas.append(texto)
		max_score = max(r[0] for r in liberal_resultados)
		ganadores = [nombre for score, nombre, _ in liberal_resultados if score == max_score]
		lineas.append("\n🏆 Más cerca de la verdad: *{}* ({} de {} aciertos)".format(
			", ".join(ganadores), max_score, total_fascists + 1))

	if hitler_lineas:
		lineas.append("")
		lineas.extend(hitler_lineas)

	if fascista_entries:
		lineas.append("")
		for predicted_uid, texto in fascista_entries:
			acierto = predicted_uid in mejores_liberales
			lineas.append(texto + "\n   ↳ {}".format("Predijo correctamente ✅" if acierto else "No acertó ❌"))

	return "\n".join(lineas)


def _repair_game_endcode_if_needed(game):
	# Cura partidas afectadas por un bug historico (choose_kill no seteaba
	# game.board.state.game_endcode) donde la partida ya termino y sus stats
	# ya se guardaron (stats_game_id seteado), pero el codigo quedo en 0.
	if game.board is None or game.board.state is None:
		return
	if game.board.state.game_endcode != 0:
		return
	game_id = getattr(game, "stats_game_id", None)
	if game_id is None:
		return
	real_endcode = StatsExtended.get_game_endcode(game_id)
	if real_endcode:
		game.board.state.game_endcode = real_endcode
		save_game(game.cid, game.groupName, game)

def _game_has_ended(game):
	if game.board is None or game.board.state is None:
		return False
	_repair_game_endcode_if_needed(game)
	return game.board.state.game_endcode != 0

def command_mvp(update: Update, context: CallbackContext):
	bot = context.bot
	uid = update.message.from_user.id
	cid = update.message.chat_id
	groupType = update.message.chat.type

	if groupType in ['group', 'supergroup']:
		game = get_game(cid)
		if game is None or game.board is None:
			bot.send_message(cid, "No hay una partida activa en este chat.")
			return
		if uid not in game.playerlist:
			bot.send_message(cid, "Debes ser un jugador de la partida para usar /mvp.")
			return
		if not _game_has_ended(game):
			bot.send_message(cid, "Todavía no terminó la partida. Esperá a que termine para votar al MVP.")
			return
		bot.send_message(cid, "Te mandé un mensaje privado para que votes al MVP. ¡Revisa tu chat privado conmigo!")
		_send_mvp_buttons(bot, game, uid)
	else:
		all_games_unfiltered = MainController.getGamesByTipo("Todos")
		all_games = {
			key: "{}: {}".format(game.groupName, game.tipo)
			for key, game in all_games_unfiltered.items()
			if uid in game.playerlist and game.board is not None and _game_has_ended(game)
		}
		if not all_games:
			bot.send_message(cid, "No tenés partidas recién terminadas donde votar al MVP.")
			return
		if len(all_games) == 1:
			game_cid = int(next(iter(all_games)))
			game = get_game(game_cid)
			_send_mvp_buttons(bot, game, uid)
		else:
			msg = "Elige el juego donde quieres votar al MVP"
			simple_choose_buttons(bot, cid, uid, uid, "chooseGameMvp", msg, all_games)

def callback_mvp_game(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_mvp_game called')
	callback = update.callback_query
	regex = re.search(r"(-?[0-9]*)\*chooseGameMvp\*(.*)\*(-?[0-9]*)", callback.data)
	game_cid = int(regex.group(2))
	uid = int(regex.group(3))
	game = get_game(game_cid)
	if game is None or game.board is None:
		bot.send_message(uid, "No hay una partida activa en ese chat.")
		return
	_send_mvp_buttons(bot, game, uid)

def _send_mvp_buttons(bot, game, uid):
	if not _game_has_ended(game):
		bot.send_message(uid, "Todavía no terminó la partida. Esperá a que termine para votar al MVP.")
		return
	strcid = str(game.cid)
	current_vote = getattr(game, "mvp_votes", {}).get(uid)
	texto = "🏅 *¿Quién fue el MVP de la partida?*\n(No podés votarte a vos mismo)"
	if current_vote in game.playerlist:
		texto += "\n\nVotaste actualmente a: *{}*. Podés cambiarlo eligiendo otro jugador mientras falten votos.".format(game.playerlist[current_vote].name)
	faltan = [p.name for u, p in game.playerlist.items() if u not in getattr(game, "mvp_votes", {})]
	if faltan:
		texto += "\n\nTodavía no votaron: {}".format(", ".join(faltan))
	btns = []
	for player_uid, player in game.playerlist.items():
		if player_uid == uid:
			continue
		btns.append([InlineKeyboardButton(player.name, callback_data=strcid + "_mvpvote_" + str(player_uid))])
	if not btns:
		bot.send_message(uid, "No hay otros jugadores a quien votar en esta partida.")
		return
	markup = InlineKeyboardMarkup(btns)
	bot.send_message(uid, texto, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

def callback_mvp_vote(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_mvp_vote called')
	callback = update.callback_query
	regex = re.search(r"(-?[0-9]*)_mvpvote_(-?[0-9]*)", callback.data)
	cid = int(regex.group(1))
	candidate_uid = int(regex.group(2))
	uid = callback.from_user.id

	game = get_game(cid)
	if game is None or game.board is None:
		bot.send_message(uid, "Esa partida ya no está activa.")
		return
	if uid not in game.playerlist:
		bot.send_message(uid, "Debes ser un jugador de la partida para votar.")
		return
	if not _game_has_ended(game):
		bot.send_message(uid, "Todavía no terminó la partida. Esperá a que termine para votar al MVP.")
		return
	if candidate_uid == uid:
		bot.send_message(uid, "No podés votarte a vos mismo como MVP.")
		return
	if candidate_uid not in game.playerlist:
		bot.send_message(uid, "Ese jugador ya no está en la partida.")
		return

	if not hasattr(game, "mvp_votes"):
		game.mvp_votes = {}
	game.mvp_votes[uid] = candidate_uid
	todos_votaron = len(game.mvp_votes) >= len(game.playerlist)
	if not todos_votaron:
		save_game(game.cid, game.groupName, game)

	bot.edit_message_text(
		"✅ ¡Listo! Votaste a *{}* como MVP de la partida.{}".format(
			game.playerlist[candidate_uid].name,
			"" if todos_votaron else " Podés cambiar tu voto en cualquier momento con /mvp mientras falten votos."),
		chat_id=callback.message.chat_id, message_id=callback.message.message_id, parse_mode=ParseMode.MARKDOWN)

	if todos_votaron:
		_finalize_mvp(bot, game)

def _finalize_mvp(bot, game):
	cid = game.cid
	try:
		reveal = format_mvp_reveal(game)
		texto = reveal if reveal is not None else "🏅 Se cerró la votación de MVP sin votos. No hay MVP esta partida."
		bot.send_message(cid, texto, ParseMode.MARKDOWN)
	except Exception as e:
		log.error("No se pudo mostrar la votación de MVP: %s" % str(e))

	try:
		nuevos_logros = StatsExtended.finalize_mvp_stats(game)
	except Exception as e:
		log.error("No se pudo finalizar las stats de MVP: %s" % str(e))
		nuevos_logros = {}

	try:
		anuncio = Achievements.format_unlock_announcement(nuevos_logros, game)
		if anuncio is not None:
			bot.send_message(cid, anuncio, ParseMode.MARKDOWN)
	except Exception as e:
		log.error("No se pudo anunciar los logros de MVP: %s" % str(e))

	if cid in GamesController.games:
		del GamesController.games[cid]
	delete_game(cid)

def command_end(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	uid = update.message.from_user.id
	groupType = update.message.chat.type

	if groupType not in ['group', 'supergroup']:
		bot.send_message(cid, "Este comando se usa en el chat del grupo.")
		return

	game = get_game(cid)
	if game is None or game.board is None:
		bot.send_message(cid, "No hay una partida en este chat.")
		return
	if uid not in game.playerlist:
		bot.send_message(cid, "Debes ser un jugador de la partida para usar /end.")
		return
	if not _game_has_ended(game):
		bot.send_message(cid, "La partida todavía no terminó, no hay nada que cerrar.")
		return

	faltan = [p.name for u, p in game.playerlist.items() if u not in getattr(game, "mvp_votes", {})]
	if faltan:
		bot.send_message(cid, "Cerrando la votación de MVP sin esperar a: {}".format(", ".join(faltan)))
	_finalize_mvp(bot, game)

def format_mvp_reveal(game):
	votes = getattr(game, "mvp_votes", {})
	tally = {}
	for voter_uid, voted_uid in votes.items():
		if voted_uid in game.playerlist:
			tally[voted_uid] = tally.get(voted_uid, 0) + 1
	if not tally:
		return None

	lineas = ["🏅 *Votación a MVP de la partida* 🏅\n"]
	for voted_uid, count in sorted(tally.items(), key=lambda kv: -kv[1]):
		nombre = game.playerlist[voted_uid].name
		lineas.append("{}: {} voto{}".format(nombre, count, "" if count == 1 else "s"))

	mvp_uid = game.compute_mvp()
	if mvp_uid is not None:
		lineas.append("\n🏆 El MVP de la partida es *{}*!".format(game.playerlist[mvp_uid].name))
	else:
		lineas.append("\n🤝 Hubo un empate en la votación, no hay MVP esta partida.")

	return "\n".join(lineas)


def command_show_stats(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	cid, uid = update.message.chat_id, update.message.from_user.id
	user_stats = MainController.load_player_stats(uid)
	if user_stats:
		jsonStr = jsonpickle.encode(user_stats)
		jsonbeuty = json.loads(jsonStr)		
		bot.send_message(cid, json.dumps(jsonbeuty, sort_keys=True, indent=4))
	else:
		bot.send_message(cid, "El usuario no tiene stats")

def command_change_stats(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	cid, uid = update.message.chat_id, update.message.from_user.id
	
	if len(args) > 1:
		stat_name = args[0].replace('_', ' ')
		amount = int(args[1])
	else:
		stat_name = "Partidas Jugadas"
		amount = 6
	try:
		MainController.change_stats(uid, "SecretHitler", stat_name, amount)
		bot.send_message(cid, "Stats actualizados")
	except Exception as e:
		bot.send_message(cid, 'No se ejecuto el comando debido a: '+str(e))

def command_leave(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	log.info('command_cancelgame called {}'.format(args))
	cid = update.message.chat_id
	uid = update.effective_user.id

	game = get_game(cid)

	if not game:
		bot.send_message(cid, '‼‼*No hay juego del que salir*‼‼', ParseMode.MARKDOWN)
	else:
		if game.board:
			bot.send_message(cid, '‼‼*El juego ya empezo y el admin no permite salir de juegos*‼‼', ParseMode.MARKDOWN)
		else:
			del game.playerlist[uid]
			bot.send_message(cid, '‼‼*Has salido exitosamente del juego*‼‼', ParseMode.MARKDOWN)


def simple_choose_buttons(bot, cid, uid, chat_donde_se_pregunta, comando_callback, mensaje_pregunta, opciones_botones, one_line = True, items_each_line = 3):
	
	#sleep(3)
	btns = []
	# Creo los botones para elegir al usuario
	if one_line:
		for key, value in opciones_botones.items():
			txtBoton = value
			datos = str(cid) + "*" + comando_callback + "*" + str(key) + "*" + str(uid)
			#if comando_callback == "announce":
			#	bot.send_message(ADMIN[0], datos)
			btns.append([InlineKeyboardButton(txtBoton, callback_data=datos)])
	else:
		btn_group = []
		for key, value in opciones_botones.items():
			txtBoton = value
			datos = str(cid) + "*" + comando_callback + "*" + str(key) + "*" + str(uid)
			#if comando_callback == "announce":
			#	bot.send_message(ADMIN[0], datos)
			btn_group.append(InlineKeyboardButton(txtBoton, callback_data=datos))
			if len(btn_group) == items_each_line:				
				btns.append(btn_group)
				btn_group = []
		# Si no completa en multiplo de items_each_line agrego los que faltan.
		if len(btn_group) > 0:
			btns.append(btn_group)
	btnMarkup = InlineKeyboardMarkup(btns)

	try:	
		#for uid in game.playerlist:
		bot.send_message(chat_donde_se_pregunta, mensaje_pregunta, reply_markup=btnMarkup, parse_mode=ParseMode.MARKDOWN)
		GamesController.simple_choose_buttons_retry = False
	except Exception as e:
		# Si tira error y estoy debugeando intento mandar de nuevo pero si no intente anteriormente
		game = get_game(cid)
		if game.is_debugging and not GamesController.simple_choose_buttons_retry:
			GamesController.simple_choose_buttons_retry = True
			simple_choose_buttons(bot, cid, ADMIN, ADMIN, comando_callback, mensaje_pregunta, opciones_botones, one_line, items_each_line)
		else:
			bot.send_message(ADMIN, 'Error en simple_choose_buttons {}'.format(e))

def command_print_stad(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	cid = update.message.chat_id
	bot.send_message(cid, f"Poblacion: {args[0]}\nExistos En poblacion: {args[1]}\nCartas sacadas: {args[2]}\nExitos: {args[3]}")
	bot.send_message(cid, PrintEstadisticas( int(args[0]), int(args[1]), int(args[2]), int(args[3])))
