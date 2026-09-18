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
from SecretHitler.Constants.Config import ADMIN, VERSION, CORTES_AUTOJA, POLITICAS_PARA_CORTAR_AUTOJA
from SecretHitler.Constants.Cards import opciones_choose_posible_role, opciones_choose_posible_role_socialista, playerSets, socialistSets
from SecretHitler.Boardgamebox.Board import Board
from SecretHitler.Boardgamebox.Game import Game
from SecretHitler.Boardgamebox.Player import Player, texto_corte_autoja
from SecretHitler.i18n import t, role_name, party_name, policy_name, preference_label
import SecretHitler.i18n as i18n
from SecretHitler.Boardgamebox.State import State
from SecretHitler.PlayerStats import PlayerStats
from SecretHitler.EstadisticsCalculator import PrintEstadisticas
import SecretHitler.StatsExtended as StatsExtended
import SecretHitler.Achievements as Achievements
import SecretHitler.GroupMembers as GroupMembers
import SecretHitler.NextGame as NextGame
# Enable logging

log.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=log.INFO)
logger = log.getLogger(__name__)

#DB Connection I made a Haroku Postgres database first
urllib.parse.uses_netloc.append("postgres")
url = urllib.parse.urlparse(os.environ["DATABASE_URL"])


# Cantidad de jugadores admitida por cada modo. La expansion socialista tiene su propia
# tabla de roles, que va de 6 a 13 jugadores.
MIN_JUGADORES_CLASICO = 5
MAX_JUGADORES_CLASICO = 10
MIN_JUGADORES_SOCIALISTA = 6
MAX_JUGADORES_SOCIALISTA = 13


def limites_jugadores(game):
	if game is not None and game.es_socialista():
		return MIN_JUGADORES_SOCIALISTA, MAX_JUGADORES_SOCIALISTA
	return MIN_JUGADORES_CLASICO, MAX_JUGADORES_CLASICO


# El listado de comandos de /help y el de simbolos de /symbols viven enteros en los
# catalogos de idioma (claves help.commands y symbols.list): es un unico bloque de
# texto por idioma, para que se pueda traducir y reordenar como una sola unidad.


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
	send_chunked_message(bot, cid, t("symbols.header", cid) + "\n" + t("symbols.list", cid))


def command_board(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	game = get_game(cid)
	if game:		
		if game.board:			
			print_board(bot, game, cid)
		else:
			bot.send_message(cid, t("cmd.board.not_started", game))
	else:
		bot.send_message(cid, t("common.no_game", cid))

def print_board(bot, game, target):
	texto = game.board.print_board(game.player_sequence, game)
	if game.es_prueba():
		# Recordatorio visible: es facil olvidarse de que la partida en curso no cuenta.
		texto = t("prueba.board_reminder", game) + "\n" + texto
	bot.send_message(target, texto, ParseMode.MARKDOWN)
		
def command_start(update: Update, context: CallbackContext):
	bot = context.bot

	cid = update.message.chat_id
	bot.send_message(cid,
		     t("start.description", cid))
	command_help(update, context)


def command_rules(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id	
	msg = t("rules.text", cid)
	bot.send_message(cid, msg, ParseMode.MARKDOWN)


def command_explainsocialista(update: Update, context: CallbackContext):
	# Explica el modo socialista y en que se diferencia del clasico. Se manda partido en
	# varios mensajes porque no entra en el limite de 4096 caracteres de Telegram.
	bot = context.bot
	cid = update.message.chat_id
	msg = t("explain.socialista_1", cid).format(min=MIN_JUGADORES_SOCIALISTA, max=MAX_JUGADORES_SOCIALISTA)
	send_chunked_message(bot, cid, msg, parse_mode=ParseMode.MARKDOWN)

	msg2 = t("explain.socialista_2", cid)
	send_chunked_message(bot, cid, msg2, parse_mode=ParseMode.MARKDOWN)


# pings the bot
def command_ping(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	bot.send_message(cid, 'pong - v0.3')

def command_version(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	bot.send_message(cid, t("cmd.version.text", cid) % VERSION)


# --- Idioma del chat (/language) ---------------------------------------------
# El idioma es del CHAT, no del jugador ni de la partida: se elige una vez en el grupo
# y desde ahi salen en ese idioma tanto los mensajes del grupo como los privados de sus
# partidas (que se resuelven por game.cid). Queda guardado en la base, asi que sobrevive
# a los reinicios y a cada /newgame.

def _aplicar_idioma(bot, cid, elegido):
	if not i18n.set_lang(cid, elegido):
		bot.send_message(cid, t("lang.save_failed", cid))
		return
	bot.send_message(cid, t("lang.changed", cid, idioma=i18n.IDIOMAS[elegido]), parse_mode=ParseMode.MARKDOWN)


def command_language(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	cid = update.message.chat_id
	uid = update.message.from_user.id
	if args:
		elegido = i18n.normalizar(args[0])
		if elegido is None:
			bot.send_message(cid, t("lang.unknown", cid, opciones=", ".join(sorted(i18n.CATALOGOS))))
			return
		_aplicar_idioma(bot, cid, elegido)
		return
	actual = i18n.get_lang(cid)
	msg = t("lang.current", cid, idioma=i18n.IDIOMAS[actual]) + "\n" + t("lang.ask", cid)
	simple_choose_buttons(bot, cid, uid, cid, "chooseLanguage", msg, dict(i18n.IDIOMAS))


def callback_language(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_language called')
	callback = update.callback_query
	regex = re.search(r"(-?[0-9]*)\*chooseLanguage\*(.*)\*(-?[0-9]*)", callback.data)
	cid, elegido = int(regex.group(1)), regex.group(2)
	if elegido not in i18n.CATALOGOS:
		return
	_aplicar_idioma(bot, cid, elegido)


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
				
				bot.send_message(cid, t("stats.query_result", cid))
				stattext = t("stats.player_header", cid).format(jugador) + \
					t("stats.games_played", cid).format(partidas_totales) + \
					t("stats.as_liberal", cid).format(partidas_totales, partidas_liberal, partidas_liberal_gano) + \
					t("stats.as_fascist", cid).format(partidas_totales, partidas_fascista, partidas_fascista_gano) + \
					t("stats.as_hitler", cid).format(partidas_totales, partidas_hitler, partidas_hitler_gano) + \
					t("stats.games_won", cid).format(partidas_totales, (partidas_hitler_gano+partidas_fascista_gano+partidas_liberal_gano), (partidas_hitler_gano+partidas_fascista_gano+partidas_liberal_gano) / (partidas_totales/100) ) + \
					t("stats.games_died", cid).format(partidas_totales, partidas_murio)	
				conn.close()
				bot.send_message(cid, stattext, ParseMode.MARKDOWN)
			else:
				bot.send_message(cid, t("stats.query_empty", cid))
			
		except Exception as e:
			bot.send_message(cid, t("error.command_failed", cid)+str(e))
	else:
		# Si el usuario no pone argumentos se muestran las estadisticas normales
		stats = MainController.get_stats(bot, cid)
		# La columna de victorias socialistas es nueva: puede no existir en bases viejas.
		vict_socialista = stats[6] if len(stats) > 6 else 0
		stattext = t("stats.header", cid) + \
				t("stats.lib_policies", cid) + str(stats[3]) + "*\n" + \
				t("stats.lib_hitler", cid) + str(stats[4]) + "*\n" + \
				t("stats.fas_policies", cid) + str(stats[2]) + "*\n" + \
				t("stats.fas_hitler_chancellor", cid) + str(stats[1]) + "*\n" + \
				t("stats.soc_policies", cid) + str(vict_socialista) + "*\n" + \
				t("stats.cancelled_games", cid) + str(stats[5]) + "*\n" + \
				t("stats.total_games", cid) + str(stats[1] + stats[2] + stats[3] + stats[4] + vict_socialista) + "*\n\n"
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
			bot.send_message(cid, t("error.command_failed", cid) + str(e))
			return

		if not matches:
			bot.send_message(cid, t("stats.no_stats_for_name", cid).format(name))
			return
		if len(matches) > 1:
			lines = [t("stats.multiple_players", cid).format(name)]
			for m_uid, m_name, total in matches:
				lines.append("- ID {0} ({1}): {2} partidas".format(m_uid, m_name, total))
			lines.append(t("stats.use_stats2_id", cid))
			bot.send_message(cid, "\n".join(lines))
			return
		target_uid = matches[0][0]

	try:
		base = StatsExtended.get_base_stats_by_uid(target_uid)
		if base is None:
			quien = t("stats.you", cid) if target_uid == caller_uid else t("stats.that_id", cid).format(target_uid)
			bot.send_message(cid, t("stats.no_new_stats", cid).format(quien))
			return

		kills = StatsExtended.get_kill_stats(target_uid)
		teammates = StatsExtended.get_teammate_stats(target_uid)
	except Exception as e:
		bot.send_message(cid, t("error.command_failed", cid) + str(e))
		return

	stattext = t("stats.header", cid) + \
		t("stats.games_played", cid).format(base["total"]) + \
		t("stats.as_liberal", cid).format(base["total"], base["liberal"], base["liberal_won"]) + \
		t("stats.as_fascist", cid).format(base["total"], base["fascista"], base["fascista_won"]) + \
		t("stats.as_hitler", cid).format(base["total"], base["hitler"], base["hitler_won"]) + \
		t("stats.games_won", cid).format(base["total"], base["gano"], (base["gano"] / base["total"]) * 100) + \
		t("stats.games_died", cid).format(base["total"], base["murio"]) + \
		t("stats.people_killed", cid).format(kills["kills_count"])

	if kills["most_killed"]:
		_, victim_name, victim_count = kills["most_killed"]
		stattext += t("stats.most_killed", cid).format(victim_name, victim_count)
	if kills["most_frequent_killer"]:
		killer_name, killer_count = kills["most_frequent_killer"]
		stattext += t("stats.most_killed_by", cid).format(killer_name, killer_count)
	if teammates["best_teammates"]:
		names = ", ".join(n for n, c in teammates["best_teammates"])
		stattext += t("stats.best_teammates", cid).format(names, teammates["best_teammates"][0][1])
	if teammates["worst_teammates"]:
		names = ", ".join(n for n, c in teammates["worst_teammates"])
		stattext += t("stats.worst_teammates", cid).format(names, teammates["worst_teammates"][0][1])

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
			bot.send_message(cid, t("error.command_failed", cid) + str(e))
			return

		if not matches:
			bot.send_message(cid, t("stats.no_stats_for_name", cid).format(name))
			return
		if len(matches) > 1:
			lines = [t("stats.multiple_players", cid).format(name)]
			for m_uid, m_name, total in matches:
				lines.append("- ID {0} ({1}): {2} partidas".format(m_uid, m_name, total))
			lines.append(t("stats.use_logros_id", cid))
			bot.send_message(cid, "\n".join(lines))
			return
		target_uid, target_name, _ = matches[0]

	try:
		texto = Achievements.format_logros_message(target_uid, target_name, cid)
	except Exception as e:
		bot.send_message(cid, t("error.command_failed", cid) + str(e))
		return

	# Chunked: con el catalogo completo el listado ya roza el limite de 4096 caracteres
	# de Telegram, y cada logro nuevo lo acerca mas.
	send_chunked_message(bot, cid, texto, parse_mode=ParseMode.MARKDOWN)

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
	help_text = t("help.header", cid) + "\n" + t("help.commands", cid)
	send_chunked_message(bot, cid, help_text)

def command_newgame(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	cid = update.message.chat_id
	groupName = update.message.chat.title	
	try:
		game = get_game(cid)
		groupType = update.message.chat.type
		if groupType not in ['group', 'supergroup']:
			bot.send_message(cid, t("cmd.newgame.add_to_group", cid))
		elif game:
			bot.send_message(cid, t("cmd.newgame.already_exists", cid))
		else:
			nuevo = Game(cid, update.message.from_user.id, groupName)
			# "/newgame socialista" arranca una partida con la Expansion Socialista.
			modo_socialista = len(args) > 0 and args[0].lower() in ("socialista", "socialist")
			if modo_socialista:
				nuevo.modo = "socialista"
			GamesController.games[cid] = nuevo
			if modo_socialista:
				bot.send_message(cid,
					u"☭" + t("cmd.newgame.created_socialist", cid) % (MIN_JUGADORES_SOCIALISTA, MAX_JUGADORES_SOCIALISTA),
					parse_mode=ParseMode.MARKDOWN)
			else:
				bot.send_message(cid, t("cmd.newgame.created", cid))
			# Aviso por privado a quienes pidieron con /nextgame que se les avise
			# apenas se cree una partida nueva en este grupo.
			interesados = NextGame.pop_waiting(cid)
			for uid_interesado, nombre_interesado in interesados:
				try:
					bot.send_message(uid_interesado, t("nextgame.notify", cid) % groupName)
				except Exception as e:
					log.error(e)

	except Exception as e:
		bot.send_message(cid, str(e))


def command_nextgame(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	uid = update.message.from_user.id
	fname = update.message.from_user.first_name.replace("_", " ")
	groupName = update.message.chat.title
	groupType = update.message.chat.type
	if groupType not in ['group', 'supergroup']:
		bot.send_message(cid, t("common.group_only", cid))
		return
	NextGame.add_waiting(cid, uid, fname)
	bot.send_message(cid, t("nextgame.registered", cid) % fname)
	try:
		bot.send_message(uid, t("nextgame.dm_ack", cid) % groupName)
	except Exception as e:
		log.error(e)
		bot.send_message(cid,
			fname + t("nextgame.no_private_chat", cid))


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
		bot.send_message(cid, t("cmd.newgame.add_to_group", cid))
	elif not game:
		bot.send_message(cid, t("common.no_game", cid))
	elif game.board:
		bot.send_message(cid, t("join.already_started", game))
	elif uid in game.playerlist:
		bot.send_message(game.cid, t("join.already_joined", game) % fname)
	elif len(game.playerlist) >= limites_jugadores(game)[1]:
		bot.send_message(game.cid, t("join.max_players", game))
	else:
		#uid = update.message.from_user.id
		player = Player(fname, uid)
		try:
			#Commented to dont disturb player during testing uncomment in production
			bot.send_message(uid, t("join.dm_welcome", game) % groupName)
			choose_posible_role(bot, cid, uid)
			
			game.add_player(uid, player)
			log.info("%s (%d) joined a game in %d" % (fname, uid, game.cid))
			# Cubre a quienes ya estaban en el grupo antes de que el tracking de /all existiera:
			# al unirse a una partida quedan registrados igual.
			GroupMembers.upsert_member(cid, uid, fname, is_bot=False, active=True)
			min_jugadores, max_jugadores = limites_jugadores(game)
			if len(game.playerlist) >= min_jugadores:
				bot.send_message(game.cid, fname + t("join.joined_enough", game) % len(game.playerlist))
			elif len(game.playerlist) == 1:
				bot.send_message(game.cid, t("join.joined_one", game) % (fname, len(game.playerlist), min_jugadores, max_jugadores))
			else:
				bot.send_message(game.cid, t("join.joined_many", game) % (fname, len(game.playerlist), min_jugadores, max_jugadores))
			# Luego dicto los jugadores que se han unido
			jugadoresActuales = t("common.players_so_far", game)
			for uid in game.playerlist:
				jugadoresActuales += "%s\n" % game.playerlist[uid].name
			bot.send_message(game.cid, jugadoresActuales)
			save_game(cid, "Game in join state", game)
		except Exception as e:
			log.error(e)
			bot.send_message(game.cid,
				fname + t("join.no_private_chat", game))


def command_startgame(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	log.info('command_startgame called')
	groupName = update.message.chat.title
	cid = update.message.chat_id
	game = get_game(cid)
	if not game:
		bot.send_message(cid, t("common.no_game", cid))
	elif game.board:
		bot.send_message(cid, t("start.already_started", game))
	elif update.message.from_user.id != game.initiator and bot.getChatMember(cid, update.message.from_user.id).status not in ("administrator", "creator"):
		bot.send_message(game.cid, t("start.only_creator", game))
	elif len(game.playerlist) < limites_jugadores(game)[0]:
		bot.send_message(game.cid, t("start.not_enough_players", game) % limites_jugadores(game))
	else:
		player_number = len(game.playerlist)
		MainController.inform_players(bot, game, game.cid, player_number)
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
			btns = [[InlineKeyboardButton(t("cancel.btn_yes", cid), callback_data="{}*confirmCancel*si*{}".format(cid, uid)),
					InlineKeyboardButton("No", callback_data="{}*confirmCancel*no*{}".format(cid, uid))]]
			bot.send_message(cid, t("cancel.confirm_ask", game), reply_markup=InlineKeyboardMarkup(btns))
		else:
			bot.send_message(cid, t("cancel.only_creator", game))
	else:
		bot.send_message(cid, t("common.no_game", cid))

def callback_cancelgame_confirm(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_cancelgame_confirm called')
	callback = update.callback_query

	regex = re.search(r"(-?[0-9]*)\*confirmCancel\*(si|no)\*(-?[0-9]*)", callback.data)
	cid, opcion, uid = int(regex.group(1)), regex.group(2), int(regex.group(3))

	if callback.from_user.id != uid:
		callback.answer(t("cancel.only_requester", cid))
		return

	if opcion == "si":
		game = get_game(cid)
		if game:
			bot.edit_message_text(t("cancel.cancelled", cid), cid, callback.message.message_id)
			MainController.end_game(bot, game, 99)
		else:
			bot.edit_message_text(t("common.no_game", cid), cid, callback.message.message_id)
	else:
		bot.edit_message_text(t("cancel.aborted", cid), cid, callback.message.message_id)

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
				bot.send_message(cid, t("vote.not_started", game))
			else:
				#If there is a time, compare it and send history of votes.
				start = game.dateinitvote
				stop = datetime.datetime.now()
				elapsed = stop - start
				if elapsed > datetime.timedelta(minutes=5):
					history_text = t("votes.history_header", game) % (game.board.state.nominated_president.name, game.board.state.nominated_chancellor.name)
					for player in game.player_sequence:
						# If the player is in the last_votes (He voted), mark him as he registered a vote
						if player.uid in game.board.state.last_votes:
							history_text += t("votes.has_voted", game) % (game.playerlist[player.uid].name)
						else:
							history_text += t("votes.has_not_voted", game) % (game.playerlist[player.uid].name)
					bot.send_message(cid, history_text, ParseMode.MARKDOWN)
				else:
					bot.send_message(cid, t("votes.wait_five_minutes", game)) 
		else:
			bot.send_message(cid, t("common.no_game", cid))
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
					bot.send_message(cid, t("mvp.everyone_voted", game))
				else:
					texto = t("mvp.still_missing_header", game)
					for p in faltan:
						texto += t("mvp.missing_line", game) % (p.name, p.uid)
					bot.send_message(cid, texto, parse_mode=ParseMode.MARKDOWN)
				return
			if not game.dateinitvote:
				# If date of init vote is null, then the voting didnt start. If it's because
				# the President still hasn't nominated a Chancellor, call him out instead of
				# just saying there's no vote yet, and resend the nomination buttons.
				presidente = game.board.state.nominated_president if game.board is not None else None
				if game.board is not None and getattr(game.board.state, "fase", None) == "choose_chancellor" and presidente is not None:
					bot.send_message(cid, t("calltovote.president_must_nominate", game) % (presidente.name, presidente.uid), parse_mode=ParseMode.MARKDOWN)
					MainController.choose_chancellor(bot, game)
				else:
					bot.send_message(cid, t("vote.not_started", game))
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
							history_text += t("calltovote.time_to_vote", game) % (game.playerlist[player.uid].name, player.uid)
							groupName = t("common.in_group", game).format(game.groupName)
							msg = t("vote.ask_group", game).format(groupName, game.board.state.nominated_president.name, game.board.state.nominated_chancellor.name)
							bot.send_message(player.uid, msg, reply_markup=voteMarkup, parse_mode=ParseMode.MARKDOWN)
					bot.send_message(cid, text=history_text, parse_mode=ParseMode.MARKDOWN)
				else:
					bot.send_message(cid, t("calltovote.wait_five_minutes", game)) 
		else:
			bot.send_message(cid, t("common.no_game", cid))
	except Exception as e:
		bot.send_message(cid, str(e))

def retract_player_vote(bot, game, uid):
	# Realiza el retiro del voto del jugador y avisa en qué grupo se retiró
	del game.board.state.last_votes[uid]
	save_game(game.cid, "retract vote Round %d" % (game.board.state.currentround), game)
	nombre = game.playerlist[uid].name
	grupo = game.groupName if (hasattr(game, 'groupName') and game.groupName) else str(game.cid)
	# Aviso en el grupo para que el resto de jugadores lo vea
	bot.send_message(game.cid, t("retract.announce", game) % nombre)
	# Le mando al jugador la confirmación (indicando el grupo) y botones para volver a votar
	strcid = str(game.cid)
	btns = [[InlineKeyboardButton("Ja", callback_data=strcid + "_Ja"),
	InlineKeyboardButton("Nein", callback_data=strcid + "_Nein")]]
	voteMarkup = InlineKeyboardMarkup(btns)
	msg = t("retract.done_group", game).format(grupo, game.board.state.nominated_president.name, game.board.state.nominated_chancellor.name)
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
				bot.send_message(uid, t("retract.no_active_vote", cid))
			elif len(retractable) == 1:
				game = get_game(int(list(retractable.keys())[0]))
				retract_player_vote(bot, game, uid)
			else:
				msg = t("retract.choose_group", cid)
				simple_choose_buttons(bot, cid, uid, uid, "chooseGameRetract", msg, retractable)
		else:
			#Check if there is a current game
			game = get_game(cid)
			if game:
				if not game.dateinitvote:
					# If date of init vote is null, then the voting didnt start
					bot.send_message(cid, t("vote.not_started", game))
				elif uid not in game.playerlist:
					bot.send_message(cid, t("common.not_in_game", game))
				elif uid not in game.board.state.last_votes:
					bot.send_message(cid, t("retract.nothing_to_retract", game))
				else:
					retract_player_vote(bot, game, uid)
			else:
				bot.send_message(cid, t("common.no_game", cid))
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
		bot.send_message(uid, t("retract.vote_closed", game))
	elif uid not in game.board.state.last_votes:
		bot.send_message(uid, t("retract.no_active_vote_there", game))
	else:
		retract_player_vote(bot, game, uid)

def _mostrar_opciones_corte_autoja(bot, game, uid):
	# Botonera para elegir cuando se corta el voto automatico. El cid que viaja en el
	# callback es el del juego, para poder encontrarlo despues.
	opciones = {clave: t("autoja.btn.%s" % clave, game, cantidad=POLITICAS_PARA_CORTAR_AUTOJA) for clave in CORTES_AUTOJA}
	msg = t("autoja.when_cut_ask", game).format(game.groupName)
	simple_choose_buttons(bot, game.cid, uid, uid, "autojacorte", msg, opciones)

def set_auto_ja(bot, game, uid, enabled):
	# Activa o desactiva el voto Ja automático del jugador para este juego
	game.playerlist[uid].auto_ja = enabled
	save_game(game.cid, "auto_ja %s Round %d" % ("on" if enabled else "off", game.board.state.currentround), game)
	if enabled:
		bot.send_message(uid,
			t("autoja.enabled", game).format(
				game.groupName, texto_corte_autoja(game.playerlist[uid].corte_autoja(), game)),
			parse_mode=ParseMode.MARKDOWN)
		_mostrar_opciones_corte_autoja(bot, game, uid)
		# Si hay una votación en curso y el jugador todavia no voto, le registro el Ja ahora mismo
		if game.dateinitvote and uid not in game.board.state.last_votes and not MainController.autoja_cortado(game, game.playerlist[uid]):
			game.board.state.last_votes[uid] = "Ja"
			save_game(game.cid, "auto_ja vote Round %d" % (game.board.state.currentround), game)
			bot.send_message(uid, t("autoja.vote_registered", game), parse_mode=ParseMode.MARKDOWN)
			if len(game.board.state.last_votes) == len(game.player_sequence):
				MainController.count_votes(bot, game)
	else:
		bot.send_message(uid, t("autoja.disabled", game).format(game.groupName), parse_mode=ParseMode.MARKDOWN)

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
				bot.send_message(uid, t("common.no_active_games", cid))
			elif len(candidatas) == 1:
				game = get_game(int(list(candidatas.keys())[0]))
				set_auto_ja(bot, game, uid, enabled)
			else:
				msg = t("autoja.choose_game_on" if enabled else "autoja.choose_game_off", cid)
				simple_choose_buttons(bot, cid, uid, uid, comando_callback, msg, candidatas)
		else:
			game = get_game(cid)
			if not game or game.board is None:
				bot.send_message(cid, t("common.no_game", cid))
			elif uid not in game.playerlist:
				bot.send_message(cid, t("common.not_in_game", game))
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
		bot.send_message(uid, t("common.not_in_that_game", game))
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
		bot.send_message(uid, t("common.not_in_that_game", game))
	else:
		set_auto_ja(bot, game, uid, False)

def callback_autoja_corte(update: Update, context: CallbackContext):
	# Guarda el criterio de corte elegido por el jugador para ese juego.
	bot = context.bot
	log.info('callback_autoja_corte called')
	callback = update.callback_query
	regex = re.search(r"(-?[0-9]*)\*autojacorte\*(.*)\*(-?[0-9]*)", callback.data)
	cid, corte, uid = int(regex.group(1)), regex.group(2), int(regex.group(3))
	game = get_game(cid)
	if not game or uid not in game.playerlist:
		bot.send_message(uid, t("common.not_in_that_game", game))
		return
	if corte not in CORTES_AUTOJA:
		return
	game.playerlist[uid].auto_ja_corte = corte
	save_game(cid, game.groupName, game)
	bot.edit_message_text(
		t("autoja.cut_set", game).format(game.groupName, texto_corte_autoja(corte, game)),
		uid, callback.message.message_id, parse_mode=ParseMode.MARKDOWN)

def command_conflicto(update: Update, context: CallbackContext):
	# Ante un conflicto en el grupo (acusaciones de que el auto-Ja tapó una votación, etc.)
	# apaga de un saque el voto automático de todos los jugadores, sin depender de que cada
	# uno se acuerde de hacer /stopautoja.
	bot = context.bot
	cid = update.message.chat_id
	try:
		game = get_game(cid)
		if not game or game.board is None:
			bot.send_message(cid, t("common.no_game", cid))
			return
		afectados = [p for p in game.playerlist.values() if getattr(p, 'auto_ja', False)]
		if not afectados:
			bot.send_message(cid, t("conflicto.nobody_had_it", game), parse_mode=ParseMode.MARKDOWN)
			return
		for p in afectados:
			p.auto_ja = False
		save_game(cid, "conflicto Round %d" % (game.board.state.currentround), game)
		bot.send_message(cid,
			t("conflicto.announce", game),
			parse_mode=ParseMode.MARKDOWN)
		for p in afectados:
			bot.send_message(p.uid,
				t("conflicto.dm", game).format(game.groupName),
				parse_mode=ParseMode.MARKDOWN)
	except Exception as e:
		bot.send_message(cid, str(e))

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
			history_text = t("history.group_header", game).format(groupName)
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
			bot.send_message(cid, t("common.no_game", cid))
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
						claimtexttohistory = t("claim.history_line", game) % (game.playerlist[uid].name, claimtext)
						bot.send_message(cid, t("claim.added", game) % (claimtext))
						game.history.append("%s" % (claimtexttohistory))
						save_game(cid, "Game in join state", game)
					else:					
						bot.send_message(cid, t("claim.need_message", game))

				else:
					bot.send_message(cid, t("claim.need_policy", game))
			else:
				bot.send_message(cid, t("claim.must_be_player", game))
				
		else:
			bot.send_message(cid, t("common.no_game", cid))
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
						claimtexttohistory = t("claim.history_line", game) % (game.playerlist[uid].name, claimtext)
						bot.send_message(uid, t("claim.added_hidden", game) % (claimtext))
						game.hiddenhistory.append("%s" % (claimtexttohistory))
					else:					
						bot.send_message(uid, t("claim.need_message", game))

				else:
					bot.send_message(uid, t("claim.need_policy_hidden", game))
			else:
				bot.send_message(uid, t("claim.not_in_any_game", game))				
	except Exception as e:
		bot.send_message(uid, str(e))
		log.error("Unknown error: " + str(e))
		
def save_game(cid, groupName, game):
	# El "groupName" que llega por parametro en la mayoria de los call sites en realidad
	# describe la accion que disparo el guardado (ej. "vote Round 3"), no el nombre del
	# grupo, asi que se ignora para la columna "name": esa siempre sale de game.groupName
	# (mantenido al dia por change_groupname() en MainController). El estado se calcula
	# aparte con Game.estado_actual() para no depender de lo que cada call site pase.
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
	estado = game.estado_actual()
	if cur.rowcount > 0:
		log.info('Updating Game')
		gamejson = jsonpickle.encode(game)
		query = "UPDATE games_secret_hitler SET name = %s, data = %s, state = %s WHERE id = %s;"
		cur.execute(query, (game.groupName, gamejson, estado, cid))
		conn.commit()
	else:
		log.info('Saving Game in DB')
		gamejson = jsonpickle.encode(game)
		query = "INSERT INTO games_secret_hitler(id , name , data, state) VALUES (%s, %s, %s, %s);"
		cur.execute(query, (cid, game.groupName, gamejson, estado))
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

		# Partidas guardadas antes de la expansion socialista no tienen este atributo.
		if not hasattr(game, "modo"):
			game.modo = "clasico"

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
			bot.send_message(cid, t("cmd.reload.add_to_group", cid))		
		else:			
			#Search game in DB
			game = load_game(cid)			
			if game:
				GamesController.games[cid] = game
				bot.send_message(cid, t("cmd.newgame.already_exists", cid))				
				
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
						bot.send_message(cid, t("reload.vote_in_progress", game))
				else:
					MainController.start_round(bot, game)
			else:				
				bot.send_message(cid, t("reload.nothing_to_reload", cid))
			
			
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
				bot.send_message(cid, t("anarchy.must_be_player", game))

		else:
			bot.send_message(cid, t("common.no_game", cid))
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
		t("fix.chancellor_announce", game).format(player.name),
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
			t("fix.president_choose_discard", game),
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
	jugadoresActuales = t("common.players_so_far", game)
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
	pregunta_arriba_botones = t("role.ask", cid)
	chat_donde_se_pregunta = uid
	# En una partida socialista se puede pedir tambien el rol Socialista.
	game = get_game(cid)
	if game is not None and game.es_socialista():
		claves = opciones_choose_posible_role_socialista
		pregunta_arriba_botones = t("role.ask_socialist", game)
	else:
		claves = opciones_choose_posible_role
	# La etiqueta de cada boton es la combinacion de roles traducida al idioma del grupo;
	# la clave que viaja en el callback sigue siendo la interna ("Liberal_Fascista").
	ctx_idioma = game if game is not None else cid
	opciones = {clave: preference_label(clave, ctx_idioma) for clave in claves}
	simple_choose_buttons(bot, cid, uid, chat_donde_se_pregunta, frase_regex, pregunta_arriba_botones, opciones)

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
			mensaje_edit = t("role.game_started", game)
		else:
			if uid in game.playerlist:
				mensaje_edit = t("role.chosen", game) % preference_label(opcion, game)
				game.playerlist[uid].preference_rol = opcion
				save_game(cid, game.groupName, game)
				choose_posible_role(bot, cid, uid)
			else:
				mensaje_edit = t("role.not_joined", game)			
	else:
		mensaje_edit = t("role.no_game", cid)		
	
	try:
		bot.edit_message_text(mensaje_edit, cid, callback.message.message_id)
	except Exception as e:
		bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)
	
	#bot.send_message(cid, "Ventana Juego: Has elegido el Rol %s" % opcion)
	#bot.send_message(uid, "Ventana Usuario: Has elegido el Rol %s" % opcion)	

def command_info(update: Update, context: CallbackContext):
	bot = context.bot
	cid, uid, groupType = update.message.chat_id, update.message.from_user.id, update.message.chat.type
	
	if groupType not in ['group', 'supergroup']:
		# En caso de no estar en un grupo y en privado con el bot muestro todos los juegos donde esta el jugador.
		# Independeinte de si pide todos, tengo que obtenerlos a todos para preguntarle cualquier quiere tener info
		all_games_unfiltered = MainController.getGamesByTipo("Todos")	
		# Me improtan los juegos que; Este el jugador, hayan sido iniciados, datinivote no sea null y que cumpla reglas del tipo de juego en particular
		all_games = {key: "{}: {}".format(game.groupName, game.tipo) for key, game in all_games_unfiltered.items() if uid in game.playerlist and game.board != None }
		msg = t("info.choose_game", cid)
		simple_choose_buttons(bot, cid, uid, uid, "chooseGameInfo", msg, all_games)
	else:
		groupName = update.message.chat.title
		game = get_game(cid)
		if game:
			if uid in game.playerlist:
				player = game.playerlist[uid]
				msg = t("info.group_header", game).format(groupName)
				msg += player.get_private_info(game)
				mis_guesses = format_my_guesses(game, uid)
				if mis_guesses is not None:
					msg += "\n\n" + mis_guesses
				bot.send_message(uid, msg, ParseMode.MARKDOWN)
			else:
				bot.send_message(cid, t("info.must_be_player", game))
		else:
			bot.send_message(cid, t("info.no_game_here", cid))

def callback_info(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_info called')
	callback = update.callback_query
	
	regex = re.search(r"(-?[0-9]*)\*chooseGameInfo\*(.*)\*(-?[0-9]*)", callback.data)
	opcion, uid = regex.group(2), int(regex.group(3))
	
	game = get_game(int(opcion))
	
	if uid in game.playerlist:
		player = game.playerlist[uid]
		msg = t("info.group_header", game).format(game.groupName)
		msg += player.get_private_info(game)
		mis_guesses = format_my_guesses(game, uid)
		if mis_guesses is not None:
			msg += "\n\n" + mis_guesses
		bot.send_message(uid, msg, ParseMode.MARKDOWN)
	else:
		bot.send_message(uid, t("info.must_be_player", game))


def _guess_num_fascists(game):
	sets = socialistSets if game.es_socialista() else playerSets
	roles = sets.get(len(game.playerlist), {}).get("roles", [])
	return sum(1 for r in roles if r == "Fascista")

def command_guess(update: Update, context: CallbackContext):
	bot = context.bot
	uid = update.message.from_user.id
	cid = update.message.chat_id
	groupType = update.message.chat.type

	if groupType in ['group', 'supergroup']:
		game = get_game(cid)
		if game is None or game.board is None:
			bot.send_message(cid, t("common.no_active_game_here", cid))
			return
		if uid not in game.playerlist:
			bot.send_message(cid, t("guess.must_be_player", game))
			return
		bot.send_message(cid, t("guess.sent_dm", game))
		_start_guess_flow(bot, game, uid)
	else:
		all_games_unfiltered = MainController.getGamesByTipo("Todos")
		all_games = {
			key: "{}: {}".format(game.groupName, game.tipo)
			for key, game in all_games_unfiltered.items()
			if uid in game.playerlist and game.board is not None
		}
		if not all_games:
			bot.send_message(cid, t("common.no_active_games", cid))
			return
		if len(all_games) == 1:
			game_cid = int(next(iter(all_games)))
			game = get_game(game_cid)
			_start_guess_flow(bot, game, uid)
		else:
			msg = t("guess.choose_game", cid)
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
		bot.send_message(uid, t("common.no_active_game_there", game))
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
		bot.send_message(uid, t("guess.already_twice", game), parse_mode=ParseMode.MARKDOWN)
		return

	player = game.playerlist.get(uid)
	role = player.role if player else None
	if role != "Fascista" and _guess_num_fascists(game) == 0:
		bot.send_message(uid, t("guess.cannot_guess", game))
		return

	if attempts_done == 0:
		if role == "Hitler":
			intro = (t("guess.intro_hitler", game))
		elif role == "Fascista":
			intro = (t("guess.intro_fascist", game))
		else:
			intro = (t("guess.intro_liberal", game))
		bot.send_message(uid, intro, parse_mode=ParseMode.MARKDOWN)
	else:
		bot.send_message(uid,
			t("guess.last_chance", game),
			parse_mode=ParseMode.MARKDOWN)

	_init_guess_progress(game, uid)
	texto, markup = _build_first_guess_prompt(game, uid)
	bot.send_message(uid, texto, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

def _build_guess_fascist_prompt(game, uid):
	progress = GamesController.guess_progress[(game.cid, uid)]
	selected = progress["fascists"]
	num_fascists = progress["num_fascists"]
	titulo = t("guess.title_hitler_teammates", game) if progress["mode"] == "hitler" else t("guess.title_fascists", game)
	texto = t("guess.pick_header", game).format(titulo, len(selected), num_fascists)
	if selected:
		nombres_elegidos = ", ".join(game.playerlist[u].name for u in selected if u in game.playerlist)
		texto += t("guess.already_picked", game).format(nombres_elegidos)
	texto += t("guess.pick_another", game)
	strcid = str(game.cid)
	btns = []
	for player_uid, player in game.playerlist.items():
		if player_uid in selected:
			continue
		btns.append([InlineKeyboardButton(player.name, callback_data=strcid + "_guessf_" + str(player_uid))])
	btns.append([InlineKeyboardButton(t("guess.btn_dont_know", game), callback_data=strcid + "_guessskip_f")])
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
		bot.send_message(uid, t("guess.game_inactive", game))
		return
	if uid not in game.playerlist:
		bot.send_message(uid, t("guess.must_be_player_guess", game))
		return

	progress = GamesController.guess_progress.get((cid, uid))
	if progress is None:
		bot.send_message(uid, t("guess.session_expired", game))
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
	texto = t("guess.who_is_hitler", game)
	btns = []
	for player_uid, player in game.playerlist.items():
		btns.append([InlineKeyboardButton(player.name, callback_data=strcid + "_guessh_" + str(player_uid))])
	btns.append([InlineKeyboardButton(t("guess.btn_dont_know", game), callback_data=strcid + "_guessskip_h")])
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
		bot.send_message(uid, t("guess.game_inactive", game))
		return
	if uid not in game.playerlist:
		bot.send_message(uid, t("guess.must_be_player_guess", game))
		return

	progress = GamesController.guess_progress.get((cid, uid))
	if progress is None:
		bot.send_message(uid, t("guess.session_expired", game))
		return
	if candidate_uid in game.playerlist:
		progress["hitler"] = candidate_uid

	texto, markup = _build_guess_confirm_prompt(game, uid)
	bot.edit_message_text(texto, chat_id=callback.message.chat_id, message_id=callback.message.message_id,
		reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

def callback_guess_skip(update: Update, context: CallbackContext):
	# "No sé": permite palpitos parciales dejando en blanco una parte del palpito.
	# Etapa "f": corta la eleccion de fascistas con los que ya haya elegido (puede ser
	# ninguno); etapa "h": no arriesga quien es Hitler; etapa "p": el fascista no
	# arriesga quien va a adivinar mejor. El campo simplemente queda como estaba en el
	# progress (lista incompleta / None) y se avanza al siguiente paso.
	bot = context.bot
	log.info('callback_guess_skip called')
	callback = update.callback_query
	regex = re.search(r"(-?[0-9]*)_guessskip_([a-z]+)", callback.data)
	cid = int(regex.group(1))
	etapa = regex.group(2)
	uid = callback.from_user.id

	game = get_game(cid)
	if game is None or game.board is None:
		bot.send_message(uid, t("guess.game_inactive", game))
		return
	if uid not in game.playerlist:
		bot.send_message(uid, t("guess.must_be_player_guess", game))
		return

	progress = GamesController.guess_progress.get((cid, uid))
	if progress is None:
		bot.send_message(uid, t("guess.session_expired", game))
		return

	if etapa == "f" and progress["mode"] == "full":
		# Dejo de pedirle fascistas, pero todavia puede arriesgar quien es Hitler.
		texto, markup = _build_guess_hitler_prompt(game, uid)
	else:
		texto, markup = _build_guess_confirm_prompt(game, uid)

	bot.edit_message_text(texto, chat_id=callback.message.chat_id, message_id=callback.message.message_id,
		reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

def _build_guess_prediction_prompt(game, uid):
	texto = t("guess.prediction_question", game)
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
	btns.append([InlineKeyboardButton(t("guess.btn_dont_know", game), callback_data=strcid + "_guessskip_p")])
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
		bot.send_message(uid, t("guess.game_inactive", game))
		return
	if uid not in game.playerlist:
		bot.send_message(uid, t("guess.must_be_player_guess", game))
		return

	progress = GamesController.guess_progress.get((cid, uid))
	if progress is None:
		bot.send_message(uid, t("guess.session_expired", game))
		return
	if candidate_uid in game.playerlist:
		progress["predicted"] = candidate_uid

	texto, markup = _build_guess_confirm_prompt(game, uid)
	bot.edit_message_text(texto, chat_id=callback.message.chat_id, message_id=callback.message.message_id,
		reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

def _build_guess_confirm_prompt(game, uid):
	progress = GamesController.guess_progress[(game.cid, uid)]
	strcid = str(game.cid)

	# "No sé" es una respuesta valida en si misma en cualquiera de los tres flujos:
	# queda registrado que el jugador no arriesgo esa parte (o ninguna). Nada se rechaza
	# por quedar en blanco; simplemente suma menos puntos en la revelacion final.
	if progress["mode"] == "hitler":
		nombres_fascistas = ", ".join(game.playerlist[u].name for u in progress["fascists"] if u in game.playerlist) or t("guess.dont_know_short", game)
		texto = t("guess.confirm_hitler", game).format(nombres_fascistas)
	elif progress["mode"] == "fascist_prediction":
		predicted = progress.get("predicted")
		nombre = game.playerlist[predicted].name if predicted in game.playerlist else t("guess.dont_know_short", game)
		texto = t("guess.confirm_prediction", game).format(nombre)
	else:
		nombres_fascistas = ", ".join(game.playerlist[u].name for u in progress["fascists"] if u in game.playerlist) or t("guess.dont_know_short", game)
		nombre_hitler = game.playerlist[progress["hitler"]].name if progress["hitler"] in game.playerlist else t("guess.dont_know_short", game)
		texto = t("guess.confirm_full", game).format(nombres_fascistas, nombre_hitler)

	btns = [
		[InlineKeyboardButton(t("guess.btn_confirm", game), callback_data=strcid + "_guessconfirm")],
		[InlineKeyboardButton(t("guess.btn_restart", game), callback_data=strcid + "_guessrestart")],
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
		bot.send_message(uid, t("guess.game_inactive", game))
		return
	progress = GamesController.guess_progress.get((cid, uid))
	if progress is None:
		bot.send_message(uid, t("guess.session_expired", game))
		return

	# Se aceptan palpitos parciales y tambien totalmente en blanco: lo que se haya dejado
	# en "No sé" se guarda vacio (lista corta / None) y simplemente suma menos puntos.
	if progress["mode"] == "hitler":
		entry = {"fascists": list(progress["fascists"])}
	elif progress["mode"] == "fascist_prediction":
		entry = {"predicted": progress.get("predicted")}
	else:
		entry = {"fascists": list(progress["fascists"]), "hitler": progress["hitler"]}

	entry["timestamp"] = datetime.datetime.now()
	entry["round"] = game.board.state.currentround

	if not hasattr(game, "guesses"):
		game.guesses = {}
	history = list(game.guesses.get(uid, []))
	history.append(entry)
	game.guesses[uid] = history
	save_game(game.cid, game.groupName, game)
	del GamesController.guess_progress[(cid, uid)]

	fecha_registro = entry["timestamp"].strftime(t("common.datetime_format", game))
	if len(history) >= 2:
		texto_final = (t("guess.saved_final", game)).format(fecha_registro)
	else:
		texto_final = (t("guess.saved", game)).format(fecha_registro)

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
		bot.send_message(uid, t("guess.game_inactive", game))
		return
	if uid not in game.playerlist:
		bot.send_message(uid, t("guess.must_be_player_guess", game))
		return

	_init_guess_progress(game, uid)
	texto, markup = _build_first_guess_prompt(game, uid)
	bot.edit_message_text(texto, chat_id=callback.message.chat_id, message_id=callback.message.message_id,
		reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

def send_chunked_message(bot, cid, text, parse_mode=None, max_len=3500):
	# Telegram limita los mensajes a 4096 caracteres; textos armados dinamicamente
	# (revelacion de /guess con muchos jugadores, etc.) pueden superarlo y el envio
	# fallaria entero. Corta por saltos de linea para no partir una entrada al medio.
	if len(text) <= max_len:
		bot.send_message(cid, text, parse_mode=parse_mode)
		return
	lineas = text.split("\n")
	chunk = ""
	for linea in lineas:
		candidato = (chunk + "\n" + linea) if chunk else linea
		if len(candidato) > max_len and chunk:
			bot.send_message(cid, chunk, parse_mode=parse_mode)
			chunk = linea
		else:
			chunk = candidato
	if chunk:
		bot.send_message(cid, chunk, parse_mode=parse_mode)

def format_guesses_reveal(game, only_uid=None):
	guesses = getattr(game, "guesses", {})
	if not guesses:
		return None

	hitler = game.get_hitler()
	hitler_uid = hitler.uid if hitler else None
	fascist_uids = {f.uid for f in game.get_fascists()}
	total_fascists = len(fascist_uids)

	liberal_resultados = []  # (score, name, texto, uid) - flujo completo, arma el ranking "mas cerca de la verdad"
	hitler_lineas = []       # (texto, uid)
	fascista_entries = []    # (predicted_uid, texto, uid)

	for guesser_uid, history in guesses.items():
		if not history:
			continue
		guess = history[-1]
		guesser = game.playerlist.get(guesser_uid)
		if guesser is None:
			continue
		nota_cambio = t("guess.changed_once", game) if len(history) > 1 else ""
		timestamp = guess.get("timestamp")
		nota_fecha = t("guess.date_note", game).format(timestamp.strftime(t("common.datetime_format", game))) if timestamp else ""
		nota_cambio += nota_fecha

		if guesser.role == "Hitler":
			guessed_fascist_uids = [u for u in guess.get("fascists", []) if u in game.playerlist]
			aciertos = [u for u in guessed_fascist_uids if u in fascist_uids]
			if guessed_fascist_uids:
				frase = t("guess.hitler_suspected", game).format(
					", ".join(game.playerlist[u].name for u in guessed_fascist_uids))
			else:
				frase = t("guess.hitler_no_guess", game)
			hitler_lineas.append((
				t("guess.hitler_line", game).format(
					guesser.name, frase, nota_cambio, len(aciertos), total_fascists),
				guesser_uid))
			continue

		if guesser.role == "Fascista":
			predicted_uid = guess.get("predicted")
			if predicted_uid in game.playerlist:
				texto = t("guess.fascist_predicted", game).format(
					guesser.name, game.playerlist[predicted_uid].name, nota_cambio)
			else:
				predicted_uid = None
				texto = t("guess.fascist_no_prediction", game).format(
					guesser.name, nota_cambio)
			fascista_entries.append((predicted_uid, texto, guesser_uid))
			continue

		# Liberal (o rol desconocido): flujo completo
		guessed_fascist_uids = [u for u in guess.get("fascists", []) if u in game.playerlist]
		guessed_hitler_uid = guess.get("hitler")

		aciertos_fascistas = [u for u in guessed_fascist_uids if u in fascist_uids]
		hitler_acierto = guessed_hitler_uid is not None and guessed_hitler_uid == hitler_uid
		score = game.compute_guess_score(guess)

		# Un palpito parcial ("No sé") deja alguna parte sin arriesgar: se distingue de haber errado.
		if guessed_fascist_uids:
			frase_fascistas = t("guess.suspected", game).format(
				", ".join(game.playerlist[u].name for u in guessed_fascist_uids))
		else:
			frase_fascistas = t("guess.no_fascist_guess", game)
		if guessed_hitler_uid in game.playerlist:
			frase_hitler = t("guess.said_hitler_was", game).format(game.playerlist[guessed_hitler_uid].name)
			detalle_hitler = t("guess.hit", game) if hitler_acierto else t("guess.miss", game)
		else:
			frase_hitler = t("guess.no_hitler_guess", game)
			detalle_hitler = t("guess.no_risk", game)

		texto = t("guess.liberal_line", game).format(
			guesser.name, frase_fascistas, frase_hitler, nota_cambio,
			len(aciertos_fascistas), total_fascists,
			detalle_hitler,
			score
		)
		liberal_resultados.append((score, guesser.name, texto, guesser_uid))

	if not liberal_resultados and not hitler_lineas and not fascista_entries:
		return None

	if only_uid is not None:
		participo = (
			any(uid == only_uid for _, _, _, uid in liberal_resultados) or
			any(uid == only_uid for _, uid in hitler_lineas) or
			any(uid == only_uid for _, _, uid in fascista_entries)
		)
		if not participo:
			return None

	titulo = t("guess.reveal_title", game) if only_uid is None else t("guess.my_reveal_title", game)
	lineas = [titulo]

	# El ranking y "quien acerto la prediccion" siempre se calculan sobre el set
	# completo de jugadores, aunque solo_uid filtre que texto se termina mostrando.
	mejores_liberales = game.compute_best_guessers()
	if liberal_resultados:
		mostrar = [r for r in liberal_resultados if only_uid is None or r[3] == only_uid]
		for _, _, texto, _ in mostrar:
			lineas.append(texto)
		if mostrar:
			max_score = max(r[0] for r in liberal_resultados)
			ganadores = [nombre for score, nombre, _, _ in liberal_resultados if score == max_score]
			lineas.append(t("guess.closest_to_truth", game).format(
				", ".join(ganadores), max_score, total_fascists + 3))

	hitler_mostrar = [texto for texto, uid in hitler_lineas if only_uid is None or uid == only_uid]
	if hitler_mostrar:
		lineas.append("")
		lineas.extend(hitler_mostrar)

	fascista_mostrar = [(p, texto) for p, texto, uid in fascista_entries if only_uid is None or uid == only_uid]
	if fascista_mostrar:
		lineas.append("")
		for predicted_uid, texto in fascista_mostrar:
			if predicted_uid is None:
				detalle = t("guess.no_risk_cap", game)
			else:
				detalle = t("guess.predicted_right", game) if predicted_uid in mejores_liberales else t("guess.predicted_wrong", game)
			lineas.append(texto + "\n   ↳ {}".format(detalle))

	return "\n".join(lineas)

def command_guessresults(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	uid = update.message.from_user.id
	groupType = update.message.chat.type

	if groupType in ['group', 'supergroup']:
		game = get_game(cid)
		if game is None or game.board is None:
			bot.send_message(cid, t("common.no_game_here", cid))
			return
		if uid not in game.playerlist:
			bot.send_message(cid, t("common.must_be_player_cmd", game))
			return
		if not _game_has_ended(game):
			bot.send_message(cid, t("common.game_not_ended", game))
			return
		_send_guessresults(bot, cid, game)
	else:
		all_games_unfiltered = MainController.getGamesByTipo("Todos")
		all_games = {
			key: "{}: {}".format(game.groupName, game.tipo)
			for key, game in all_games_unfiltered.items()
			if uid in game.playerlist and game.board is not None and _game_has_ended(game)
		}
		if not all_games:
			bot.send_message(cid, t("common.no_recent_games", cid))
			return
		if len(all_games) == 1:
			game_cid = int(next(iter(all_games)))
			game = get_game(game_cid)
			_send_guessresults(bot, uid, game)
		else:
			msg = t("guessresults.choose_game", cid)
			simple_choose_buttons(bot, cid, uid, uid, "chooseGameGuessResults", msg, all_games)

def callback_guessresults_game(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_guessresults_game called')
	callback = update.callback_query
	regex = re.search(r"(-?[0-9]*)\*chooseGameGuessResults\*(.*)\*(-?[0-9]*)", callback.data)
	game_cid = int(regex.group(2))
	uid = int(regex.group(3))
	game = get_game(game_cid)
	if game is None or game.board is None:
		bot.send_message(uid, t("common.no_active_game_there", game))
		return
	_send_guessresults(bot, uid, game)

def _send_guessresults(bot, target_cid, game):
	reveal = format_guesses_reveal(game)
	if reveal is None:
		bot.send_message(target_cid, t("guessresults.nobody_guessed", game))
	else:
		send_chunked_message(bot, target_cid, reveal, parse_mode=ParseMode.MARKDOWN)

def command_miguess(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	uid = update.message.from_user.id
	groupType = update.message.chat.type

	if groupType in ['group', 'supergroup']:
		game = get_game(cid)
		if game is None or game.board is None:
			bot.send_message(cid, t("common.no_game_here", cid))
			return
		if uid not in game.playerlist:
			bot.send_message(cid, t("common.must_be_player_cmd", game))
			return
		if not _game_has_ended(game):
			bot.send_message(cid, t("common.game_not_ended", game))
			return
		_send_miguess(bot, game, uid)
	else:
		all_games_unfiltered = MainController.getGamesByTipo("Todos")
		all_games = {
			key: "{}: {}".format(game.groupName, game.tipo)
			for key, game in all_games_unfiltered.items()
			if uid in game.playerlist and game.board is not None and _game_has_ended(game)
		}
		if not all_games:
			bot.send_message(cid, t("common.no_recent_games", cid))
			return
		if len(all_games) == 1:
			game_cid = int(next(iter(all_games)))
			game = get_game(game_cid)
			_send_miguess(bot, game, uid)
		else:
			msg = t("miguess.choose_game", cid)
			simple_choose_buttons(bot, cid, uid, uid, "chooseGameMiguess", msg, all_games)

def callback_miguess_game(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('callback_miguess_game called')
	callback = update.callback_query
	regex = re.search(r"(-?[0-9]*)\*chooseGameMiguess\*(.*)\*(-?[0-9]*)", callback.data)
	game_cid = int(regex.group(2))
	uid = int(regex.group(3))
	game = get_game(game_cid)
	if game is None or game.board is None:
		bot.send_message(uid, t("common.no_active_game_there", game))
		return
	_send_miguess(bot, game, uid)

def _send_miguess(bot, game, uid):
	reveal = format_guesses_reveal(game, only_uid=uid)
	if reveal is None:
		bot.send_message(uid, t("miguess.you_didnt_guess", game))
	else:
		send_chunked_message(bot, uid, reveal, parse_mode=ParseMode.MARKDOWN)

def format_my_guesses(game, uid):
	# Muestra ambos intentos de /guess del jugador (no solo el definitivo), sin
	# revelar si acertaron o no: eso mostraria implicitamente roles/afiliaciones
	# reales antes de que la partida termine. La correccion final vive en
	# /miguess y /guessresults, que si estan gateados a que la partida ya termino.
	history = getattr(game, "guesses", {}).get(uid)
	if not history:
		return None
	player = game.playerlist.get(uid)
	if player is None:
		return None

	lineas = [t("myguess.title", game)]
	for i, entry in enumerate(history, start=1):
		etiqueta = t("myguess.attempt", game).format(i) + (t("myguess.final", game) if i == len(history) else "")
		timestamp = entry.get("timestamp")
		nota_fecha = t("guess.date_note", game).format(timestamp.strftime(t("common.datetime_format", game))) if timestamp else ""

		nombres = ", ".join(game.playerlist[u].name for u in entry.get("fascists", []) if u in game.playerlist)
		if player.role == "Hitler":
			if nombres:
				texto = t("myguess.hitler_line", game).format(etiqueta, nota_fecha, nombres)
			else:
				texto = t("myguess.hitler_none", game).format(etiqueta, nota_fecha)
		elif player.role == "Fascista":
			predicted_uid = entry.get("predicted")
			if predicted_uid in game.playerlist:
				texto = t("myguess.fascist_line", game).format(
					etiqueta, nota_fecha, game.playerlist[predicted_uid].name)
			else:
				texto = t("myguess.fascist_none", game).format(etiqueta, nota_fecha)
		else:
			frase_fascistas = t("myguess.suspected", game).format(nombres) if nombres else t("myguess.no_fascists", game)
			hitler_uid = entry.get("hitler")
			if hitler_uid in game.playerlist:
				frase_hitler = t("myguess.said_hitler", game).format(game.playerlist[hitler_uid].name)
			else:
				frase_hitler = t("myguess.no_hitler", game)
			texto = t("myguess.line", game).format(etiqueta, nota_fecha, frase_fascistas, frase_hitler)

		lineas.append(texto)

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

def command_prueba(update: Update, context: CallbackContext):
	# Alterna si la partida de este grupo es "de prueba" (no se guardan estadisticas,
	# no se otorgan logros y no hay MVP) o vale. Siempre avisa en que modo quedo.
	bot = context.bot
	cid = update.message.chat_id
	uid = update.message.from_user.id
	groupType = update.message.chat.type

	if groupType not in ['group', 'supergroup']:
		bot.send_message(cid, t("common.group_chat_only", cid))
		return

	game = get_game(cid)
	if game is None:
		bot.send_message(cid, t("common.no_game", cid))
		return
	if game.board is not None and _game_has_ended(game):
		# La partida ya se cerro: sus estadisticas ya se guardaron (o ya se descartaron),
		# asi que cambiar el modo a esta altura no haria nada.
		bot.send_message(cid,
			t("prueba.already_ended", game))
		return
	if game.playerlist and uid not in game.playerlist and uid != game.initiator and uid != ADMIN:
		bot.send_message(cid, t("prueba.only_player", game))
		return

	game.es_partida_de_prueba = not game.es_prueba()
	save_game(cid, game.groupName, game)
	bot.send_message(cid,
		t("prueba.on", game) if game.es_prueba() else t("prueba.off", game),
		parse_mode=ParseMode.MARKDOWN)

def command_mvp(update: Update, context: CallbackContext):
	bot = context.bot
	uid = update.message.from_user.id
	cid = update.message.chat_id
	groupType = update.message.chat.type

	if groupType in ['group', 'supergroup']:
		game = get_game(cid)
		if game is None or game.board is None:
			bot.send_message(cid, t("common.no_active_game_here", cid))
			return
		if uid not in game.playerlist:
			bot.send_message(cid, t("mvp.must_be_player", game))
			return
		if game.es_prueba():
			bot.send_message(cid, t("prueba.on", game), parse_mode=ParseMode.MARKDOWN)
			return
		if not _game_has_ended(game):
			bot.send_message(cid, t("mvp.not_ended", game))
			return
		bot.send_message(cid, t("mvp.sent_dm", game))
		_send_mvp_buttons(bot, game, uid)
	else:
		all_games_unfiltered = MainController.getGamesByTipo("Todos")
		all_games = {
			key: "{}: {}".format(game.groupName, game.tipo)
			for key, game in all_games_unfiltered.items()
			if uid in game.playerlist and game.board is not None and _game_has_ended(game)
			and not game.es_prueba()
		}
		if not all_games:
			bot.send_message(cid, t("mvp.no_recent_games", cid))
			return
		if len(all_games) == 1:
			game_cid = int(next(iter(all_games)))
			game = get_game(game_cid)
			_send_mvp_buttons(bot, game, uid)
		else:
			msg = t("mvp.choose_game", cid)
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
		bot.send_message(uid, t("common.no_active_game_there", game))
		return
	_send_mvp_buttons(bot, game, uid)

def _send_mvp_buttons(bot, game, uid):
	if game.es_prueba():
		bot.send_message(uid, t("prueba.on", game), parse_mode=ParseMode.MARKDOWN)
		return
	if not _game_has_ended(game):
		bot.send_message(uid, t("mvp.not_ended", game))
		return
	strcid = str(game.cid)
	current_vote = getattr(game, "mvp_votes", {}).get(uid)
	texto = t("mvp.ask", game)
	if current_vote in game.playerlist:
		texto += t("mvp.current_vote", game).format(game.playerlist[current_vote].name)
	faltan = [p.name for u, p in game.playerlist.items() if u not in getattr(game, "mvp_votes", {})]
	if faltan:
		texto += t("mvp.not_voted_yet", game).format(", ".join(faltan))
	btns = []
	for player_uid, player in game.playerlist.items():
		if player_uid == uid:
			continue
		btns.append([InlineKeyboardButton(player.name, callback_data=strcid + "_mvpvote_" + str(player_uid))])
	if not btns:
		bot.send_message(uid, t("mvp.no_other_players", game))
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
		bot.send_message(uid, t("guess.game_inactive", game))
		return
	if uid not in game.playerlist:
		bot.send_message(uid, t("mvp.must_be_player_vote", game))
		return
	if game.es_prueba():
		bot.send_message(uid, t("prueba.on", game), parse_mode=ParseMode.MARKDOWN)
		return
	if not _game_has_ended(game):
		bot.send_message(uid, t("mvp.not_ended", game))
		return
	if candidate_uid == uid:
		bot.send_message(uid, t("mvp.no_self_vote", game))
		return
	if candidate_uid not in game.playerlist:
		bot.send_message(uid, t("mvp.player_gone", game))
		return

	if not hasattr(game, "mvp_votes"):
		game.mvp_votes = {}
	game.mvp_votes[uid] = candidate_uid
	todos_votaron = len(game.mvp_votes) >= len(game.playerlist)
	if not todos_votaron:
		save_game(game.cid, game.groupName, game)

	bot.edit_message_text(
		t("mvp.voted", game).format(
			game.playerlist[candidate_uid].name,
			"" if todos_votaron else t("mvp.can_change", game)),
		chat_id=callback.message.chat_id, message_id=callback.message.message_id, parse_mode=ParseMode.MARKDOWN)

	if todos_votaron:
		_finalize_mvp(bot, game)

def _finalize_mvp(bot, game):
	cid = game.cid
	try:
		reveal = format_mvp_reveal(game)
		texto = reveal if reveal is not None else t("mvp.no_votes", game)
		bot.send_message(cid, texto, ParseMode.MARKDOWN)
	except Exception as e:
		log.error("No se pudo mostrar la votación de MVP: %s" % str(e))

	try:
		detalle = format_mvp_votes_detail(game)
		if detalle is not None:
			bot.send_message(ADMIN, detalle, parse_mode=ParseMode.MARKDOWN)
	except Exception as e:
		log.error("No se pudo informar al admin el detalle de votos de MVP: %s" % str(e))

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
		bot.send_message(cid, t("common.group_chat_only", cid))
		return

	game = get_game(cid)
	if game is None or game.board is None:
		bot.send_message(cid, t("common.no_game_here", cid))
		return
	if uid not in game.playerlist:
		bot.send_message(cid, t("end.must_be_player", game))
		return
	if game.es_prueba():
		bot.send_message(cid, t("prueba.on", game), parse_mode=ParseMode.MARKDOWN)
		return
	if not _game_has_ended(game):
		bot.send_message(cid, t("end.not_ended", game))
		return

	faltan = [p.name for u, p in game.playerlist.items() if u not in getattr(game, "mvp_votes", {})]
	if faltan:
		bot.send_message(cid, t("end.closing_without", game).format(", ".join(faltan)))
	_finalize_mvp(bot, game)

def format_mvp_reveal(game):
	tally = game.compute_mvp_tally()
	if not tally:
		return None

	lineas = [t("mvp.reveal_title", game)]
	for voted_uid, count in sorted(tally.items(), key=lambda kv: -kv[1]):
		nombre = game.playerlist[voted_uid].name
		plantilla = t("mvp.tally_plural", game) if count != 1 else t("mvp.tally_singular", game)
		lineas.append(plantilla.format(nombre, count))

	mvp_uids = game.compute_mvps()
	if len(mvp_uids) > 1:
		nombres = ", ".join("*{}*".format(game.playerlist[u].name) for u in mvp_uids)
		lineas.append(t("mvp.co_mvps", game).format(nombres))
	elif mvp_uids:
		lineas.append(t("mvp.the_mvp", game).format(game.playerlist[mvp_uids[0]].name))
	else:
		lineas.append(t("mvp.tie", game))

	return "\n".join(lineas)

def format_mvp_votes_detail(game):
	# A diferencia de format_mvp_reveal (publico, solo el conteo agregado), esto
	# muestra quien voto a quien: se manda solo al ADMIN cuando se cierra la
	# votacion, nunca al grupo, para no exponer los votos individuales de nadie.
	votes = getattr(game, "mvp_votes", {})
	if not votes:
		return None
	lineas = ["🗳 *Detalle de votos MVP - {}*".format(game.groupName)]
	for voter_uid, voted_uid in votes.items():
		voter = game.playerlist.get(voter_uid)
		voted = game.playerlist.get(voted_uid)
		voter_name = voter.name if voter else str(voter_uid)
		voted_name = voted.name if voted else str(voted_uid)
		lineas.append("{} → {}".format(voter_name, voted_name))
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
		bot.send_message(cid, t("stats.user_has_no_stats", cid))

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
		bot.send_message(cid, t("stats.updated", cid))
	except Exception as e:
		bot.send_message(cid, t("error.command_failed", cid)+str(e))

def command_leave(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	log.info('command_cancelgame called {}'.format(args))
	cid = update.message.chat_id
	uid = update.effective_user.id

	game = get_game(cid)

	if not game:
		bot.send_message(cid, t("leave.no_game", cid), ParseMode.MARKDOWN)
	else:
		if game.board:
			bot.send_message(cid, t("leave.already_started", game), ParseMode.MARKDOWN)
		else:
			del game.playerlist[uid]
			bot.send_message(cid, t("leave.success", game), ParseMode.MARKDOWN)


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
		if game is not None and game.is_debugging and not GamesController.simple_choose_buttons_retry:
			GamesController.simple_choose_buttons_retry = True
			simple_choose_buttons(bot, cid, ADMIN, ADMIN, comando_callback, mensaje_pregunta, opciones_botones, one_line, items_each_line)
		else:
			bot.send_message(ADMIN, 'Error en simple_choose_buttons {}'.format(e))

def command_print_stad(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	cid = update.message.chat_id
	bot.send_message(cid, t("stad.params", cid).format(args[0], args[1], args[2], args[3]))
	bot.send_message(cid, PrintEstadisticas(int(args[0]), int(args[1]), int(args[2]), int(args[3]), cid))
