#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Julian Schrittwieser,  Leviatas"

import json
import logging as log
import random
import re
from random import randrange
from time import sleep

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update, BotCommand
from telegram.ext import (Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext)


import SecretHitler.Commands as Commands
from SecretHitler.Constants.Cards import playerSets
from SecretHitler.Constants.Cards import socialistSets
from SecretHitler.Constants.Cards import CENSURA_DESDE
from SecretHitler.Constants.Config import ADMIN, VERSION, POLITICAS_PARA_CORTAR_AUTOJA
from SecretHitler.Boardgamebox.Game import Game
from SecretHitler.Boardgamebox.Player import Player
from SecretHitler.i18n import t, role_name, party_name, policy_name
import SecretHitler.i18n as i18n
from SecretHitler.PlayerStats import PlayerStats
import SecretHitler.GamesController as GamesController
import SecretHitler.StatsExtended as StatsExtended
import SecretHitler.Achievements as Achievements
import SecretHitler.GroupMembers as GroupMembers
import SecretHitler.HistoryPrefs as HistoryPrefs

import datetime
import jsonpickle
import os
import psycopg2
from psycopg2 import sql
import urllib.parse

import traceback
import sys

from Utils import command_status

from telegram.utils.helpers import mention_html
# Enable logging

log.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s Secret Hitler',
        level=log.INFO)


logger = log.getLogger(__name__)

#DB Connection I made a Haroku Postgres database first
urllib.parse.uses_netloc.append("postgres")
url = urllib.parse.urlparse(os.environ["DATABASE_URL"])


'''
cur = conn.cursor()
query = "SELECT ...."
cur.execute(query)
'''



##
#
# Beginning of round
#
##

def start_round(bot, game):        
	Commands.save_game(game.cid, "Saved Round %d" % (game.board.state.currentround + 1), game)
	log.info('start_round called')
	# Starting a new round makes the current round to go up    
	game.board.state.currentround += 1
	
	if game.board.state.chosen_president is None:
		game.board.state.nominated_president = game.player_sequence[game.board.state.player_counter]
	else:
		game.board.state.nominated_president = game.board.state.chosen_president
		game.board.state.chosen_president = None

	# El Presidente de la Camara dura una sola sesion legislativa (modo socialista).
	game.board.state.chairman = None
	# Ninguna propuesta socialista puede sobrevivir a la ronda en la que se hizo.
	game.board.state.socialist_proposal = None

	Commands.print_board(bot, game, game.cid)
	msgtext =  t("round.next_president", game) % (game.board.state.nominated_president.name, game.board.state.nominated_president.uid, game.board.state.nominated_president.name)
	bot.send_message(game.cid, msgtext, ParseMode.MARKDOWN)
	choose_chancellor(bot, game)
	# --> nominate_chosen_chancellor --> vote --> handle_voting --> count_votes --> voting_aftermath --> draw_policies
	# --> choose_policy --> pass_two_policies --> choose_policy --> enact_policy --> start_round


def choose_chancellor(bot, game):
	log.info('choose_chancellor called')
	strcid = str(game.cid)
	pres_uid = 0
	chan_uid = 0
	btns = []
	if game.board.state.president is not None:
		pres_uid = game.board.state.president.uid
	if game.board.state.chancellor is not None:
		chan_uid = game.board.state.chancellor.uid
	for uid in game.playerlist:
		# If there are only five players left in the
		# game, only the last elected Chancellor is
		# ineligible to be Chancellor Candidate; the
		# last President may be nominated.
		if len(game.player_sequence) > 5:
			if uid != game.board.state.nominated_president.uid and game.playerlist[uid].is_dead == False and uid != pres_uid and uid != chan_uid:
				name = game.playerlist[uid].name
				btns.append([InlineKeyboardButton(name, callback_data=strcid + "_chan_" + str(uid))])
		else:
			if uid != game.board.state.nominated_president.uid and game.playerlist[uid].is_dead == False and uid != chan_uid:
				name = game.playerlist[uid].name
				btns.append([InlineKeyboardButton(name, callback_data=strcid + "_chan_" + str(uid))])

	chancellorMarkup = InlineKeyboardMarkup(btns)
	#descomentar al entrar en produccion

	if game.is_debugging:
		Commands.print_board(bot, game, ADMIN)
		bot.send_message(ADMIN, t("chancellor.nominate_prompt", game), parse_mode=ParseMode.MARKDOWN, reply_markup=chancellorMarkup)      
	else:
		Commands.print_board(bot, game, game.board.state.nominated_president.uid)
		groupName = ""
		if hasattr(game, 'groupName'):
			groupName += t("common.in_group", game).format(game.groupName)
		msg = t("chancellor.nominate_prompt_group", game).format(groupName)
		bot.send_message(game.board.state.nominated_president.uid, msg, parse_mode=ParseMode.MARKDOWN, reply_markup=chancellorMarkup)

	game.board.state.fase = "choose_chancellor"
	Commands.save_game(game.cid, "choose_chancellor Round %d" % (game.board.state.currentround), game)

def nominate_chosen_chancellor(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('nominate_chosen_chancellor called')
	log.info(update.callback_query.data)
	callback = update.callback_query
	regex = re.search("(-[0-9]*)_chan_([0-9]*)", callback.data)
	cid = int(regex.group(1))
	chosen_uid = int(regex.group(2))
	#if(game.is_debugging):
	#    chosen_uid = ADMIN   
	try:
		game = Commands.get_game(cid)

		if callback.from_user.id != game.board.state.nominated_president.uid:
			bot.edit_message_text(t("chancellor.not_president", game), callback.from_user.id, callback.message.message_id)
			return

		game.board.state.nominated_chancellor = game.playerlist[chosen_uid]
		log.info("El Presidente %s (%d) nominó a %s (%d)" % (
					game.board.state.nominated_president.name, game.board.state.nominated_president.uid,
					game.board.state.nominated_chancellor.name, game.board.state.nominated_chancellor.uid))
		bot.edit_message_text(t("chancellor.you_nominated", game) % game.board.state.nominated_chancellor.name,
					callback.from_user.id, callback.message.message_id)
		bot.send_message(game.cid,
					t("chancellor.nominated_announce", game) % (
					game.board.state.nominated_president.name, game.board.state.nominated_chancellor.name))
		# Se setea la fase y se guarda antes de votar, porque vote() puede
		# terminar la votación en el momento si todos los votos ya estan
		# registrados por /startautoja, y eso avanza la ronda a otra fase.
		game.board.state.fase = "vote"
		Commands.save_game(game.cid, "vote Round %d" % (game.board.state.currentround), game)
		vote(bot, game)
	except AttributeError as e:
		log.error("nominate_chosen_chancellor: Game or board should not be None! Eror: " + str(e))
	except Exception as e:
		log.error("Unknown error: " + repr(e))
		log.exception(e)
		
def is_zona_hitler(game):
	# Zona Hitler: ya se promulgaron 3 politicas fascistas
	return game.board.state.fascist_track >= 3


def politicas_promulgadas(game):
	# Todas las politicas que ya estan en la mesa, sin importar el color (en modo socialista
	# la pista socialista tambien cuenta). Es tambien el numero de ronda: sumar solo liberales
	# y fascistas repetia el numero cada vez que se promulgaba una politica socialista.
	state = game.board.state
	return state.liberal_track + state.fascist_track + getattr(state, "socialist_track", 0)


def autoja_cortado(game, player):
	# Si el voto automatico Ja de este jugador ya no corresponde. El criterio lo elige cada
	# jugador en /startautoja: cortar por Zona Hitler, por cantidad de politicas promulgadas,
	# o por cualquiera de las dos (el default).
	corte = player.corte_autoja()
	por_fascistas = is_zona_hitler(game)
	por_politicas = politicas_promulgadas(game) >= POLITICAS_PARA_CORTAR_AUTOJA
	if corte == "fascistas":
		return por_fascistas
	if corte == "politicas":
		return por_politicas
	return por_fascistas or por_politicas

def vote(bot, game):
	log.info('vote called')
	#When voting starts we start the counter to see later with the vote command if we can see you voted.
	game.dateinitvote = datetime.datetime.now()

	strcid = str(game.cid)
	btns = [[InlineKeyboardButton("Ja", callback_data=strcid + "_Ja"),
	InlineKeyboardButton("Nein", callback_data=strcid + "_Nein")]]
	voteMarkup = InlineKeyboardMarkup(btns)
	for uid in game.playerlist:
		if not game.playerlist[uid].is_dead and not game.is_debugging:
			if game.playerlist[uid] is not game.board.state.nominated_president:
				# the nominated president already got the board before nominating a chancellor
				Commands.print_board(bot, game, uid)
			groupName = ""
			if hasattr(game, 'groupName'):
				groupName += t("common.in_group", game).format(game.groupName)
			msg = t("vote.ask_group", game).format(groupName, game.board.state.nominated_president.name, game.board.state.nominated_chancellor.name)
			if getattr(game.playerlist[uid], 'auto_ja', False) and not autoja_cortado(game, game.playerlist[uid]):
				game.board.state.last_votes[uid] = "Ja"
				msg += t("vote.autoja_registered", game)
			bot.send_message(uid, msg,	reply_markup=voteMarkup, parse_mode=ParseMode.MARKDOWN)

	if len(game.board.state.last_votes) == len(game.player_sequence):
		count_votes(bot, game)

def handle_voting(update: Update, context: CallbackContext):
	bot = context.bot
	callback = update.callback_query
	log.info('handle_voting called: %s' % callback.data)
	regex = re.search("(-[0-9]*)_(.*)", callback.data)
	cid = int(regex.group(1))
	answer = regex.group(2)
	strcid = regex.group(1)
	try:
		game = Commands.get_game(cid)
		uid = callback.from_user.id
		#
		if game.dateinitvote is None:
			bot.edit_message_text(t("vote.not_voting_time", game), uid, callback.message.message_id)
			return

		bot.edit_message_text(t("vote.thanks", game) % (
			answer, game.board.state.nominated_president.name, game.board.state.nominated_chancellor.name), uid,
			callback.message.message_id)
		log.info("Player %s (%d) voted %s" % (callback.from_user.first_name, uid, answer))

		#if uid not in game.board.state.last_votes:
		game.board.state.last_votes[uid] = answer

		#Allow player to change his vote
		btns = [[InlineKeyboardButton("Ja", callback_data=strcid + "_Ja"),
				InlineKeyboardButton("Nein", callback_data=strcid + "_Nein")]]
		voteMarkup = InlineKeyboardMarkup(btns)
		 
		groupName = ""
		
		if hasattr(game, 'groupName'):
			groupName += t("common.in_group", game).format(game.groupName)

		msg = t("vote.change_ask_group", game).format(groupName, game.board.state.nominated_president.name, game.board.state.nominated_chancellor.name)
		bot.send_message(uid, msg, reply_markup=voteMarkup, parse_mode=ParseMode.MARKDOWN)
		Commands.save_game(game.cid, "vote Round %d" % (game.board.state.currentround), game)
		if len(game.board.state.last_votes) == len(game.player_sequence):
			count_votes(bot, game)
	except Exception as e:
		log.error(str(e))

def entrada_votacion(game, votos, valor_ja, valor_nein, encabezado, resultado, empate_pierde_ja=True):
	# Las votaciones se guardan en game.history como un dict estructurado, no como
	# texto ya armado, para que /history pueda mostrarlas compactas o extendidas
	# (ver render_entrada_historial). Los votos van en orden de turno, normalizados
	# a "ja"/"nein" asi la de formula (Ja/Nein) y la de anarquia (Si/No) se
	# renderizan igual. Es una lista de listas (no un dict por uid) para que
	# jsonpickle no tenga nada que stringificar.
	# encabezado y resultado ya van renderizados: quedan en el idioma que tenia el
	# grupo cuando paso, igual que el resto de las lineas del historial.
	lista_votos = []
	for player in game.player_sequence:
		voto = votos.get(player.uid)
		if voto == valor_ja:
			lista_votos.append([game.playerlist[player.uid].name, "ja"])
		elif voto == valor_nein:
			lista_votos.append([game.playerlist[player.uid].name, "nein"])
	return {
		"tipo": "votacion",
		"encabezado": encabezado,
		"votos": lista_votos,
		"empate_pierde_ja": empate_pierde_ja,
		"resultado": resultado,
	}


def _nombre_para_historial(nombre):
	# Se sacan "_" (Markdown) y "`" (cerraria el bloque de codigo).
	return nombre.replace("_", " ").replace("`", "'")


def resumen_de_votos(game, lista_votos, empate_pierde_ja=True):
	# Version compacta de la votacion: una linea por resultado
	# con la cantidad y los nombres de quienes votaron asi.
	# Los votantes de la minoria van en `codigo` para que se note quienes fueron.
	# En un empate se destaca a los que perdieron: en la votacion de formula el
	# empate la rechaza (perdio el Ja); en la de anarquia el empate la aprueba
	# (perdio el No), por eso empate_pierde_ja=False ahi.
	# Si todos votaron lo mismo solo se muestra "Votos X: Todos".
	ja = [_nombre_para_historial(nombre) for nombre, voto in lista_votos if voto == "ja"]
	nein = [_nombre_para_historial(nombre) for nombre, voto in lista_votos if voto == "nein"]
	if ja and not nein:
		return t("vote.summary_all_ja", game) + "\n"
	if nein and not ja:
		return t("vote.summary_all_nein", game) + "\n"
	if len(ja) == len(nein):
		destacar_ja = empate_pierde_ja
	else:
		destacar_ja = len(ja) < len(nein)

	def nombres(lista, destacar):
		if destacar:
			return ", ".join("`%s`" % nombre for nombre in lista)
		return ", ".join(lista)

	texto = t("vote.summary_ja", game) % len(ja)
	if ja:
		texto += ": " + nombres(ja, destacar_ja)
	texto += t("vote.summary_nein", game) % len(nein)
	if nein:
		texto += ": " + nombres(nein, not destacar_ja)
	return texto + "\n"


def detalle_de_votos(game, lista_votos):
	# Version extendida: cada jugador con su voto, uno abajo del otro, en orden de turno.
	texto = ""
	for nombre, voto in lista_votos:
		sufijo = "vote.voted_ja_suffix" if voto == "ja" else "vote.voted_nein_suffix"
		texto += _nombre_para_historial(nombre) + t(sufijo, game)
	return texto


def render_entrada_historial(game, entrada, extendido=False):
	# Las entradas de game.history son texto, salvo las votaciones (ver
	# entrada_votacion). Las votaciones guardadas antes de este cambio son texto
	# con el resumen compacto ya armado, asi que salen igual en ambos modos.
	if isinstance(entrada, dict) and entrada.get("tipo") == "votacion":
		if extendido:
			votos_text = detalle_de_votos(game, entrada["votos"])
		else:
			votos_text = resumen_de_votos(game, entrada["votos"], entrada.get("empate_pierde_ja", True))
		return entrada["encabezado"] + votos_text + entrada["resultado"]
	return str(entrada)


def count_votes(bot, game):
	# La votacion ha finalizado.
	game.dateinitvote = None
	# La votacion ha finalizado.
	log.info('count_votes called')
	voting_text = ""
	voting_success = False
	for player in game.player_sequence:
		nombre_jugador = game.playerlist[player.uid].name.replace("_", " ")
		if game.board.state.last_votes[player.uid] == "Ja":
			voting_text += nombre_jugador + t("vote.voted_ja_suffix", game)
		elif game.board.state.last_votes[player.uid] == "Nein":
			voting_text += nombre_jugador + t("vote.voted_nein_suffix", game)
	if list(game.board.state.last_votes.values()).count("Ja") > (
		len(game.player_sequence) / 2):  # because player_sequence doesnt include dead
		# VOTING WAS SUCCESSFUL
		log.info("Voting successful")
		resultado_text = t("vote.hail", game) % (
			game.board.state.nominated_president.name, game.board.state.nominated_president.uid, 
				game.board.state.nominated_chancellor.name, game.board.state.nominated_chancellor.uid)
		voting_text += resultado_text
		game.board.state.chancellor = game.board.state.nominated_chancellor
		game.board.state.president = game.board.state.nominated_president
		game.board.state.nominated_president = None
		game.board.state.nominated_chancellor = None
		voting_success = True
		
		bot.send_message(game.cid, voting_text, ParseMode.MARKDOWN)
		bot.send_message(game.cid, t("vote.no_talking", game))
		game.history.append(entrada_votacion(game, game.board.state.last_votes, "Ja", "Nein",
			t("history.round_header", game) % (politicas_promulgadas(game) + 1, game.board.state.failed_votes + 1),
			resultado_text))
		#log.info(game.history[game.board.state.currentround])
		voting_aftermath(bot, game, voting_success)
	else:
		log.info("Voting failed")
		resultado_text = t("vote.rejected", game) % (
			game.board.state.nominated_president.name, game.board.state.nominated_chancellor.name)
		voting_text += resultado_text
		game.board.state.nominated_president = None
		game.board.state.nominated_chancellor = None
		game.board.state.failed_votes += 1
		bot.send_message(game.cid, voting_text)
		game.history.append(entrada_votacion(game, game.board.state.last_votes, "Ja", "Nein",
			t("history.round_header", game) % (politicas_promulgadas(game) + 1, game.board.state.failed_votes),
			resultado_text))
		#log.info(game.history[game.board.state.currentround])
		if game.board.state.failed_votes == 3:
			do_anarchy(bot, game)
		else:
			voting_aftermath(bot, game, voting_success)


def voting_aftermath(bot, game, voting_success):
	log.info('voting_aftermath called')
	game.board.state.last_votes = {}
	if voting_success:
		if game.board.state.fascist_track >= 3 and game.board.state.chancellor.role == "Hitler":
			# fascists win, because Hitler was elected as chancellor after 3 fascist policies
			game.board.state.game_endcode = -2
			end_game(bot, game, game.board.state.game_endcode)
		else:
			if game.board.state.fascist_track >= 3 and game.board.state.chancellor.role != "Hitler" and game.board.state.chancellor not in game.board.state.not_hitlers:
				game.board.state.not_hitlers.append(game.board.state.chancellor)
			# voting was successful and Hitler was not nominated as chancellor after 3 fascist policies
			start_legislative_session(bot, game)
	else:
		#Commands.print_board(bot, game, game.cid)
		start_next_round(bot, game)


def start_legislative_session(bot, game):
	# En el modo socialista el canciller elige un Presidente de la Camara antes de la sesion
	# legislativa; con la Censura activa ese paso desaparece y se roban las politicas directamente.
	if game.board.es_socialista() and not game.board.hay_censura():
		choose_chairman(bot, game)
	else:
		draw_policies(bot, game)


def choose_chairman(bot, game):
	log.info('choose_chairman called')
	strcid = str(game.cid)
	btns = []
	for uid in game.playerlist:
		if game.playerlist[uid].is_dead:
			continue
		if uid in (game.board.state.president.uid, game.board.state.chancellor.uid):
			continue
		btns.append([InlineKeyboardButton(game.playerlist[uid].name, callback_data=strcid + "_chair_" + str(uid))])

	if not btns:
		# Sin nadie fuera del gobierno no hay a quien darle la Camara.
		bot.send_message(game.cid, t("chairman.nobody_available", game))
		draw_policies(bot, game)
		return

	chairmanMarkup = InlineKeyboardMarkup(btns)
	bot.send_message(game.cid,
		t("chairman.must_choose", game) % game.board.state.chancellor.name + u"\U0001F3DB")
	msg = t("chairman.choose_prompt", game)
	if game.is_debugging:
		bot.send_message(ADMIN, msg, reply_markup=chairmanMarkup)
	else:
		bot.send_message(game.board.state.chancellor.uid, msg, reply_markup=chairmanMarkup)
	game.board.state.fase = "choose_chairman"
	Commands.save_game(game.cid, "choose_chairman Round %d" % (game.board.state.currentround), game)


def choose_chosen_chairman(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('choose_chosen_chairman called')
	callback = update.callback_query
	regex = re.search("(-[0-9]*)_chair_([0-9]*)", callback.data)
	cid = int(regex.group(1))
	chosen_uid = int(regex.group(2))
	try:
		game = Commands.get_game(cid)

		if callback.from_user.id != game.board.state.chancellor.uid and not game.is_debugging:
			bot.edit_message_text(t("chairman.not_chancellor", game), callback.from_user.id, callback.message.message_id)
			return
		if game.board.state.chairman is not None:
			# Ya se eligio en esta ronda: ignoro el click repetido.
			return

		chosen = game.playerlist[chosen_uid]
		game.board.state.chairman = chosen
		bot.edit_message_text(t("chairman.you_chose", game) % chosen.name,
			callback.from_user.id, callback.message.message_id)
		bot.send_message(game.cid,
			t("chairman.chosen_announce", game) % (game.board.state.chancellor.name, chosen.name))
		game.history.append(t("chairman.chosen_announce", game) % (game.board.state.chancellor.name, chosen.name))

		# Mezclo antes de espiar para que la carta que ve sea la que realmente va a robar el presidente.
		shuffle_policy_pile(bot, game)
		top_policy = game.board.policies[0]
		bot.send_message(ADMIN if game.is_debugging else chosen.uid,
			t("chairman.peek", game) % (game.groupName, top_policy), parse_mode=ParseMode.MARKDOWN)
		game.hiddenhistory.append(t("chairman.peek_hidden", game) % (chosen.name, top_policy))
		draw_policies(bot, game)
	except AttributeError as e:
		log.error("choose_chosen_chairman: Game or board should not be None! Error: " + str(e))
	except Exception as e:
		log.error("Unknown error: " + repr(e))
		log.exception(e)


def draw_policies(bot, game):
	log.info('draw_policies called')
	strcid = str(game.cid)
	game.board.state.veto_refused = False
	# shuffle discard pile with rest if rest < 3
	shuffle_policy_pile(bot, game)
	btns = []
	hiddenhistory_text = ""
	for i in range(3):
		game.board.state.drawn_policies.append(game.board.policies.pop(0))
	for policy in game.board.state.drawn_policies:
		btns.append([InlineKeyboardButton(policy_name(policy, game).title(), callback_data=strcid + "_" + policy)])
		hiddenhistory_text += policy_name(policy, game).title() + " "
	hiddenhistory_text[:-1]
	# Guardo Historial secreto
	game.hiddenhistory.append((t("hidden.president_drew", game) % (politicas_promulgadas(game) + 1, game.board.state.failed_votes + 1, game.board.state.president.name) ) + hiddenhistory_text)
	choosePolicyMarkup = InlineKeyboardMarkup(btns)
	if not game.is_debugging:
		bot.send_message(game.board.state.president.uid, f"{game.groupName}" + t("legis.draw_prompt", game),
			reply_markup=choosePolicyMarkup)
	else:
		bot.send_message(ADMIN, f"{game.groupName}" + t("legis.draw_prompt", game),
			reply_markup=choosePolicyMarkup)
	game.board.state.fase = "legislating president discard"
	Commands.save_game(game.cid, "legislating president discard Round %d" % (game.board.state.currentround), game)

def choose_policy(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('choose_policy called')
	callback = update.callback_query
	regex = re.search("(-[0-9]*)_(.*)", callback.data)
	cid = int(regex.group(1))
	answer = regex.group(2)
	try:
		game = Commands.get_game(cid)	
		strcid = str(game.cid)
		uid = callback.from_user.id

		# Solo el presidente y el canciller pueden elegir politica.
		if uid not in [game.board.state.chancellor.uid, game.board.state.president.uid]:
			msg = t("legis.not_president_nor_chancellor", game)
			bot.edit_message_text(msg, uid,	callback.message.message_id)
			return

		# Si hay 3 politicas veo que sea el presidente el que descarte.
		if len(game.board.state.drawn_policies) == 3 and uid == game.board.state.president.uid:
			log.info("Player %s (%d) discarded %s" % (callback.from_user.first_name, uid, answer))
			politics = ','.join(policy_name(p, game) for p in game.board.state.drawn_policies)
			bot.edit_message_text(t("legis.you_drew_discard", game) % (politics , policy_name(answer, game)), uid,
			callback.message.message_id)
			# remove policy from drawn cards and add to discard pile, pass the other two policies
			# Grabo en Hidden History que descarta el presidente.
			game.hiddenhistory.append(t("hidden.president_discarded", game) + policy_name(answer, game))
			for i in range(3):
				if game.board.state.drawn_policies[i] == answer:
					game.board.discards.append(game.board.state.drawn_policies.pop(i))                                
					break
			pass_two_policies(bot, game)
		elif len(game.board.state.drawn_policies) == 2 and uid == game.board.state.chancellor.uid:
			# Si el canciller elije el boton de veto
			if answer == "veto" :
				log.info("Player %s (%d) suggested a veto" % (callback.from_user.first_name, uid))
				bot.edit_message_text(t("veto.you_suggested", game) % game.board.state.president.name, uid,
					callback.message.message_id)
				bot.send_message(game.cid,
					t("veto.suggested_announce", game) % (
					game.board.state.chancellor.name, game.board.state.president.name))

				btns = [[InlineKeyboardButton(t("veto.btn_yes", game), callback_data=strcid + "_yesveto")],
				[InlineKeyboardButton(t("veto.btn_no", game), callback_data=strcid + "_noveto")]]

				vetoMarkup = InlineKeyboardMarkup(btns)
				bot.send_message(game.board.state.president.uid,
					t("veto.ask_president", game) % game.board.state.chancellor.name,
					reply_markup=vetoMarkup)
			else:
				# Si el canciller promulga...
				log.info("Player %s (%d) chose a %s policy" % (callback.from_user.first_name, uid, answer))
				bot.edit_message_text(t("legis.policy_will_be_enacted", game) % policy_name(answer, game), uid,
				callback.message.message_id)
				# remove policy from drawn cards and enact, discard the other card
				for i in range(2):
					if game.board.state.drawn_policies[i] == answer:
						game.board.state.drawn_policies.pop(i)
						break
				game.board.discards.append(game.board.state.drawn_policies.pop(0))
				assert len(game.board.state.drawn_policies) == 0
				enact_policy(bot, game, answer, False)
		else:
			log.error("choose_policy: drawn_policies should be 3 or 2, but was " + str(
				len(game.board.state.drawn_policies)))
	except Exception as e:
		log.error("choose_policy:" + str(e))

def pass_two_policies(bot, game):
	log.info('pass_two_policies called')
	strcid = str(game.cid)
	btns = []
	for policy in game.board.state.drawn_policies:
		btns.append([InlineKeyboardButton(policy_name(policy, game).title(), callback_data=strcid + "_" + policy)])
	if game.board.state.fascist_track == 5 and not game.board.state.veto_refused:
		btns.append([InlineKeyboardButton(t("veto.btn_veto", game), callback_data=strcid + "_veto")])
		choosePolicyMarkup = InlineKeyboardMarkup(btns)
		bot.send_message(game.cid,
			t("legis.passed_two", game) % (
			game.board.state.president.name, game.board.state.chancellor.name))
		bot.send_message(game.board.state.chancellor.uid,
			t("legis.choose_enact_with_veto", game) % game.board.state.president.name,
		reply_markup=choosePolicyMarkup)
	elif game.board.state.veto_refused:
		choosePolicyMarkup = InlineKeyboardMarkup(btns)
		bot.send_message(game.board.state.chancellor.uid,
			t("legis.veto_refused_choose", game) % game.board.state.president.name,
			reply_markup=choosePolicyMarkup)
	elif game.board.state.fascist_track < 5:
		bot.send_message(game.cid,
			t("legis.passed_two", game) % (
			game.board.state.president.name, game.board.state.chancellor.name))
		choosePolicyMarkup = InlineKeyboardMarkup(btns)
		if not game.is_debugging:
			bot.send_message(game.board.state.chancellor.uid,
				t("legis.choose_enact", game) % game.board.state.president.name,
				reply_markup=choosePolicyMarkup)
		else:
			bot.send_message(ADMIN,
				t("legis.choose_enact", game) % game.board.state.president.name,
				reply_markup=choosePolicyMarkup)	
	
	game.board.state.fase = "legislating choose chancellor"
	Commands.save_game(game.cid, "legislating choose chancellor Round %d" % (game.board.state.currentround), game)

def enact_policy(bot, game, policy, anarchy):
	log.info('enact_policy called')
	if policy == "liberal":
		game.board.state.liberal_track += 1
	elif policy == "fascista":
		game.board.state.fascist_track += 1
	elif policy == "socialista":
		game.board.state.socialist_track += 1
	game.board.state.failed_votes = 0  # reset counter
	if not anarchy:
		texto_promulgada = t("legis.enacted_announce", game) % (game.board.state.president.name, game.board.state.chancellor.name, policy_name(policy, game))
		bot.send_message(game.cid, texto_promulgada)
		game.history.append(texto_promulgada)
		if not hasattr(game, "formula_history"):
			game.formula_history = []
		game.formula_history.append({
			"round": game.board.state.currentround,
			"president_uid": game.board.state.president.uid,
			"chancellor_uid": game.board.state.chancellor.uid,
			"policy": policy,
		})
	else:
		texto_anarquia = t("anarchy.top_enacted", game) % policy_name(policy, game)
		bot.send_message(game.cid, texto_anarquia)
		game.history.append(texto_anarquia)
	#sleep(2)
	# end of round
	if game.board.state.liberal_track == getattr(game.board, "liberal_track_size", 5):
		game.board.state.game_endcode = 1
		end_game(bot, game, game.board.state.game_endcode)  # liberals win with 5 liberal policies
	if game.board.state.fascist_track == 6:
		game.board.state.game_endcode = -1
		end_game(bot, game, game.board.state.game_endcode)  # fascists win with 6 fascist policies
	if game.board.es_socialista() and game.board.state.socialist_track == game.board.socialist_track_size():
		game.board.state.game_endcode = 3
		end_game(bot, game, game.board.state.game_endcode)  # socialists win with their whole track
	#sleep(3)
	# End of legislative session, shuffle if necessary
	shuffle_policy_pile(bot, game)
	if game.board.state.game_endcode != 0:
		return
	if policy == "socialista":
		# Los poderes socialistas los usa el partido y no el presidente, asi que tambien
		# se ejecutan cuando la politica salio por anarquia.
		socialist_action(bot, game)
	elif not anarchy:
		if policy == "fascista":
			action = game.board.fascist_track_actions[game.board.state.fascist_track - 1]
			if action is None and game.board.state.fascist_track == 6:
				pass
			elif action == None:
				start_next_round(bot, game)
			elif action == "policy":
				bot.send_message(game.cid,
					t("power.policy_title", game) + u"\U0001F52E" + t("power.policy_body", game) % game.board.state.president.name)
				game.history.append(t("power.policy_history", game) % game.board.state.president.name)
				action_policy(bot, game)                
			elif action == "kill":
				msg = t("power.kill_title", game) + u"\U0001F5E1" + t("power.kill_body", game) % game.board.state.president.name
				bot.send_message(game.cid, msg)
				game.board.state.fase = "legislating power kill"
				Commands.save_game(game.cid, "legislating power kill Round %d" % (game.board.state.currentround), game)
				action_kill(bot, game)				
			elif action == "inspect":
				bot.send_message(game.cid,
					t("power.inspect_title", game) + u"\U0001F50E" + t("power.inspect_body", game) % game.board.state.president.name)
				game.board.state.fase = "legislating power inspect"
				Commands.save_game(game.cid, "legislating power inspect Round %d" % (game.board.state.currentround), game)				
				action_inspect(bot, game)
			elif action == "choose":
				bot.send_message(game.cid,
					t("power.choose_title", game) + u"\U0001F454" + t("power.choose_body", game) % game.board.state.president.name)
				game.board.state.fase = "legislating power choose"
				Commands.save_game(game.cid, "legislating power choose Round %d" % (game.board.state.currentround), game)
				action_choose(bot, game)
		else:
			start_next_round(bot, game)
	else:
		start_next_round(bot, game)


def choose_veto(update: Update, context: CallbackContext):
	bot = context.bot
	callback = update.callback_query
	regex = re.search("(-[0-9]*)_(.*)", callback.data)
	cid = int(regex.group(1))
	answer = regex.group(2)
	game = Commands.get_game(cid)
	uid = callback.from_user.id
	if answer == "yesveto":
		log.info("Player %s (%d) accepted the veto" % (callback.from_user.first_name, uid))
		bot.edit_message_text(t("veto.you_accepted", game), uid, callback.message.message_id)
		bot.send_message(game.cid,
							t("veto.accepted_announce", game) % (
								game.board.state.president.name, game.board.state.chancellor.name))
		game.board.discards += game.board.state.drawn_policies
		game.board.state.drawn_policies = []
		game.board.state.failed_votes += 1
		shuffle_policy_pile(bot, game)  
		if game.board.state.failed_votes == 3:
			do_anarchy(bot, game)
		else:                
			start_next_round(bot, game)
	elif answer == "noveto":
		log.info("Player %s (%d) declined the veto" % (callback.from_user.first_name, uid))
		game.board.state.veto_refused = True
		bot.edit_message_text(t("veto.you_rejected", game), uid, callback.message.message_id)
		bot.send_message(game.cid,
							t("veto.rejected_announce", game) % (
								game.board.state.president.name, game.board.state.chancellor.name))
		pass_two_policies(bot, game)
	else:
		log.error("choose_veto: Callback data can either be \"veto\" or \"noveto\", but not %s" % answer)
    


def do_anarchy(bot, game):
	#log.info('do_anarchy called')	
	bot.send_message(game.cid, t("anarchy.announce", game))
	game.board.state.president = None
	game.board.state.chancellor = None
	top_policy = game.board.policies.pop(0)
	game.board.state.last_votes = {}
	enact_policy(bot, game, top_policy, True)


def action_policy(bot, game):
    log.info('action_policy called')
    topPolicies = ""
    # shuffle discard pile with rest if rest < 3
    shuffle_policy_pile(bot, game)
    for i in range(3):
        topPolicies += policy_name(game.board.policies[i], game) + "\n"
    bot.send_message(game.board.state.president.uid,
                     t("power.policy_peek_result", game) % topPolicies)
    start_next_round(bot, game)


def action_kill(bot, game):
	log.info('action_kill called')
	strcid = str(game.cid)
	btns = []
	for uid in game.playerlist:
		if uid != game.board.state.president.uid and game.playerlist[uid].is_dead == False:
			name = game.playerlist[uid].name
			btns.append([InlineKeyboardButton(name, callback_data=strcid + "_kill_" + str(uid))])

	killMarkup = InlineKeyboardMarkup(btns)
	Commands.print_board(bot, game, game.board.state.president.uid)
	bot.send_message(game.board.state.president.uid,
		t("power.kill_prompt", game),
		reply_markup=killMarkup)


def choose_kill(update: Update, context: CallbackContext):
	
    bot = context.bot
    callback = update.callback_query
    regex = re.search("(-[0-9]*)_kill_(.*)", callback.data)
    cid = int(regex.group(1))
    answer = int(regex.group(2))
    try:
        game = Commands.get_game(cid)
        chosen = game.playerlist[answer]
        chosen.is_dead = True
        chosen.killed_by_uid = game.board.state.president.uid
        if game.player_sequence.index(chosen) <= game.board.state.player_counter:
            game.board.state.player_counter -= 1
        game.player_sequence.remove(chosen)
        game.board.state.dead += 1
        log.info("El jugador %s (%d) mató a %s (%d)" % (
            callback.from_user.first_name, callback.from_user.id, chosen.name, chosen.uid))
        bot.edit_message_text(t("kill.you_killed", game) % chosen.name, callback.from_user.id, callback.message.message_id)
        if chosen.role == "Hitler":
            bot.send_message(game.cid, t("kill.hitler_announce", game) % (game.board.state.president.name, chosen.name))
            game.board.state.game_endcode = 2
            end_game(bot, game, 2)
        else:
            bot.send_message(game.cid,
                             t("kill.not_hitler_announce", game) % (
                                 game.board.state.president.name, chosen.name, chosen.name))
            groupName = ""
            if hasattr(game, 'groupName'):
                groupName += t("common.in_group", game).format(game.groupName)
            bot.send_message(chosen.uid,
                t("kill.you_are_dead", game).format(groupName) % game.board.state.president.name,
                parse_mode=ParseMode.MARKDOWN)
            game.history.append(t("kill.not_hitler_history", game) % (game.board.state.president.name, chosen.name))
            start_next_round(bot, game)
    except:
        log.error("choose_kill: Game or board should not be None!")


def action_choose(bot, game):
    log.info('action_choose called')
    strcid = str(game.cid)
    btns = []

    for uid in game.playerlist:
        if uid != game.board.state.president.uid and game.playerlist[uid].is_dead == False:
            name = game.playerlist[uid].name
            btns.append([InlineKeyboardButton(name, callback_data=strcid + "_choo_" + str(uid))])

    inspectMarkup = InlineKeyboardMarkup(btns)
    Commands.print_board(bot, game, game.board.state.president.uid)
    bot.send_message(game.board.state.president.uid,
                     t("power.choose_prompt", game),
                     reply_markup=inspectMarkup)


def choose_choose(update: Update, context: CallbackContext):
	
    bot = context.bot
    callback = update.callback_query
    regex = re.search("(-[0-9]*)_choo_(.*)", callback.data)
    cid = int(regex.group(1))
    answer = int(regex.group(2))
    try:
        game = Commands.get_game(cid)
        chosen = game.playerlist[answer]
        game.board.state.chosen_president = chosen
        log.info(
            "El jugador %s (%d) ha elegido a %s (%d) como próximo Presidente" % (
                callback.from_user.first_name, callback.from_user.id, chosen.name, chosen.uid))
        bot.edit_message_text(t("choose.you_chose", game) % chosen.name, callback.from_user.id,
                              callback.message.message_id)
        bot.send_message(game.cid,
                         t("choose.announce", game) % (
                             game.board.state.president.name, chosen.name))
        game.history.append(t("choose.announce", game) % (game.board.state.president.name, chosen.name))
        start_next_round(bot, game)
    except:
        log.error("choose_choose: Game or board should not be None!")


def action_inspect(bot, game):
    log.info('action_inspect called')
    strcid = str(game.cid)
    btns = []
    for uid in game.playerlist:
        if uid != game.board.state.president.uid and game.playerlist[uid].is_dead == False and game.playerlist[uid].was_investigated == False:
            name = game.playerlist[uid].name
            btns.append([InlineKeyboardButton(name, callback_data=strcid + "_insp_" + str(uid))])

    inspectMarkup = InlineKeyboardMarkup(btns)
    Commands.print_board(bot, game, game.board.state.president.uid)
    bot.send_message(game.board.state.president.uid,
                     t("power.inspect_prompt", game),
                     reply_markup=inspectMarkup)


def choose_inspect(update: Update, context: CallbackContext):
	
    bot = context.bot
    callback = update.callback_query
    regex = re.search("(-[0-9]*)_insp_(.*)", callback.data)
    cid = int(regex.group(1))
    answer = int(regex.group(2))
    try:
        game = Commands.get_game(cid)
        chosen = game.playerlist[answer]
        log.info(
            "Player %s (%d) inspects %s (%d)'s party membership (%s)" % (
                callback.from_user.first_name, callback.from_user.id, chosen.name, chosen.uid,
                chosen.party))
        bot.edit_message_text(t("inspect.result", game) % (chosen.name, party_name(chosen.party, game)),
                              callback.from_user.id,
                              callback.message.message_id)
        chosen.was_investigated = True
        bot.send_message(game.cid, t("inspect.announce", game) % (game.board.state.president.name, chosen.name))
        game.history.append(t("inspect.announce", game) % (game.board.state.president.name, chosen.name))
        start_next_round(bot, game)
    except:
        log.error("choose_inspect: Game or board should not be None!")


##
#
# Poderes socialistas (expansion socialista)
#
# A diferencia de los presidenciales, no los usa el presidente sino el partido socialista:
# los botones se le mandan a todos los socialistas vivos y decide el primero que contesta.
# Escucha, Reclutamiento y Congreso son acciones nocturnas y por lo tanto secretas: el grupo
# se entera de que el poder se uso, pero no sobre quien (eso queda en el historial oculto).
# La Confesion en cambio pasa a la vista de todos.
#
##

def socialist_action(bot, game):
	log.info('socialist_action called')
	if game.board.state.socialist_track == CENSURA_DESDE:
		bot.send_message(game.cid,
			u"\U0001F576" + t("soc.censorship_announce", game))
		game.history.append(t("soc.censorship_history", game))

	action = game.board.socialist_track_actions[game.board.state.socialist_track - 1]
	if action == "escucha":
		action_escucha(bot, game)
	elif action == "reclutamiento":
		action_reclutamiento(bot, game)
	elif action == "plan_quinquenal":
		action_plan_quinquenal(bot, game)
	elif action == "congreso":
		action_congreso(bot, game)
	elif action == "confesion":
		action_confesion(bot, game)
	else:
		start_next_round(bot, game)


def _offer_socialist_power(bot, game, power, prefijo, mensaje, es_elegible):
	# Le manda los mismos botones a todos los socialistas vivos. La guarda contra el doble
	# click (que dos socialistas elijan a la vez) esta en _claim_socialist_power.
	socialistas = game.get_socialist_team(only_alive=True)
	btns = []
	for uid in game.playerlist:
		jugador = game.playerlist[uid]
		if jugador.is_dead or not es_elegible(jugador):
			continue
		btns.append([InlineKeyboardButton(jugador.name, callback_data="%d_%s_%d" % (game.cid, prefijo, uid))])

	if not socialistas or not btns:
		bot.send_message(game.cid, t("soc.power_skipped", game))
		game.board.state.pending_socialist_power = None
		start_next_round(bot, game)
		return

	game.board.state.pending_socialist_power = power
	markup = InlineKeyboardMarkup(btns)
	if game.is_debugging:
		bot.send_message(ADMIN, mensaje, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)
	else:
		for socialista in socialistas:
			bot.send_message(socialista.uid, "%s\n%s" % (game.groupName, mensaje), reply_markup=markup, parse_mode=ParseMode.MARKDOWN)
	game.board.state.fase = "legislating socialist power " + power
	Commands.save_game(game.cid, "legislating socialist power %s Round %d" % (power, game.board.state.currentround), game)


def _claim_socialist_power(game, uid, power):
	# True solo para el socialista vivo que llega primero a proponer. Mientras haya una
	# propuesta en votacion nadie puede proponer otra.
	if getattr(game.board.state, "pending_socialist_power", None) != power:
		return False
	if getattr(game.board.state, "socialist_proposal", None) is not None:
		return False
	if not game.is_debugging and uid not in [p.uid for p in game.get_socialist_team(only_alive=True)]:
		return False
	return True


def _avisar_socialistas(bot, game, texto, excepto_uid=None):
	for socialista in game.get_socialist_team(only_alive=True):
		if socialista.uid == excepto_uid:
			continue
		bot.send_message(ADMIN if game.is_debugging else socialista.uid, texto, parse_mode=ParseMode.MARKDOWN)
		if game.is_debugging:
			break


def _ofrecer_poder_socialista(bot, game, power):
	# Manda (o vuelve a mandar, si una propuesta fue rechazada) la botonera del poder.
	if power == "escucha":
		_offer_socialist_power(bot, game, "escucha", "socbug",
			u"\U0001F41B" + t("soc.escucha_pick", game),
			lambda jugador: jugador.party != "socialista")
	elif power == "reclutamiento":
		_offer_socialist_power(bot, game, "reclutamiento", "socrec",
			u"\u270A" + t("soc.reclutamiento_pick", game),
			lambda jugador: jugador.party != "socialista")
	elif power == "confesion":
		presidente = game.board.state.president
		_offer_socialist_power(bot, game, "confesion", "socconf",
			u"\U0001F4D6" + t("soc.confesion_pick", game) % presidente.name,
			lambda jugador: jugador.uid != presidente.uid)


def _proponer_objetivo(bot, game, power, proposer_uid, chosen):
	# Las decisiones socialistas son del partido entero: el que elige solo propone y el poder
	# se aplica unicamente si TODOS los demas socialistas vivos estan de acuerdo. Con un solo
	# socialista vivo no hay a quien consultarle y se aplica derecho.
	votantes = [p for p in game.get_socialist_team(only_alive=True) if p.uid != proposer_uid]
	if not votantes or game.is_debugging:
		_aplicar_poder_socialista(bot, game, power, chosen)
		return

	game.board.state.socialist_proposal = {
		"power": power,
		"target": chosen.uid,
		"proposer": proposer_uid,
		"approvals": [],
	}
	strcid = str(game.cid)
	btns = [[InlineKeyboardButton(t("soc.btn_agree", game), callback_data=strcid + "_socvoto_si"),
		InlineKeyboardButton("No", callback_data=strcid + "_socvoto_no")]]
	markup = InlineKeyboardMarkup(btns)
	proponente = game.playerlist[proposer_uid].name
	for votante in votantes:
		bot.send_message(votante.uid,
			t("soc.proposal_ask", game) % (
				game.groupName, proponente, chosen.name),
			reply_markup=markup, parse_mode=ParseMode.MARKDOWN)
	bot.send_message(proposer_uid,
		t("soc.proposal_waiting", game) % chosen.name,
		parse_mode=ParseMode.MARKDOWN)
	game.board.state.fase = "legislating socialist proposal " + power
	Commands.save_game(game.cid, "legislating socialist proposal %s Round %d" % (power, game.board.state.currentround), game)


def handle_socialist_vote(update: Update, context: CallbackContext):
	bot = context.bot
	callback = update.callback_query
	regex = re.search("(-[0-9]*)_socvoto_(si|no)", callback.data)
	cid = int(regex.group(1))
	voto = regex.group(2)
	try:
		game = Commands.get_game(cid)
		uid = callback.from_user.id
		propuesta = getattr(game.board.state, "socialist_proposal", None)
		if propuesta is None:
			bot.edit_message_text(t("soc.decision_resolved", game), uid, callback.message.message_id)
			return
		votantes = [p.uid for p in game.get_socialist_team(only_alive=True) if p.uid != propuesta["proposer"]]
		if uid not in votantes or uid in propuesta["approvals"]:
			return

		chosen = game.playerlist[propuesta["target"]]
		power = propuesta["power"]
		if voto == "no":
			# Sin unanimidad la propuesta se cae y se vuelve a abrir la eleccion para todos.
			log.info("Propuesta socialista de %s rechazada por %d" % (chosen.name, uid))
			bot.edit_message_text(t("soc.you_rejected", game) % chosen.name, uid, callback.message.message_id)
			game.board.state.socialist_proposal = None
			_avisar_socialistas(bot, game,
				t("soc.someone_rejected", game) % chosen.name,
				excepto_uid=uid)
			_ofrecer_poder_socialista(bot, game, power)
			return

		propuesta["approvals"].append(uid)
		bot.edit_message_text(t("soc.you_accepted", game) % chosen.name, uid, callback.message.message_id)
		if len(propuesta["approvals"]) < len(votantes):
			faltan = len(votantes) - len(propuesta["approvals"])
			plantilla = t("soc.waiting_plural", game) if faltan > 1 else t("soc.waiting_singular", game)
			bot.send_message(propuesta["proposer"], plantilla % (faltan, chosen.name))
			Commands.save_game(game.cid, "socialist proposal vote Round %d" % game.board.state.currentround, game)
			return

		# Unanimidad: se aplica el poder.
		game.board.state.socialist_proposal = None
		_avisar_socialistas(bot, game, t("soc.party_agreed", game) % chosen.name)
		_aplicar_poder_socialista(bot, game, power, chosen)
	except Exception as e:
		log.error("handle_socialist_vote: " + repr(e))
		log.exception(e)


def _aplicar_poder_socialista(bot, game, power, chosen):
	# Se llama solo cuando la decision ya esta tomada (unanimidad, o un unico socialista vivo).
	game.board.state.pending_socialist_power = None
	game.board.state.socialist_proposal = None
	if power == "escucha":
		_aplicar_escucha(bot, game, chosen)
	elif power == "reclutamiento":
		_aplicar_reclutamiento(bot, game, chosen)
	elif power == "confesion":
		_aplicar_confesion(bot, game, chosen)
	else:
		start_next_round(bot, game)


def action_escucha(bot, game):
	log.info('action_escucha called')
	bot.send_message(game.cid,
		t("soc.escucha_title", game) + u"\U0001F41B" + t("soc.escucha_body", game))
	_ofrecer_poder_socialista(bot, game, "escucha")


def choose_escucha(update: Update, context: CallbackContext):
	bot = context.bot
	callback = update.callback_query
	regex = re.search("(-[0-9]*)_socbug_(.*)", callback.data)
	cid = int(regex.group(1))
	answer = int(regex.group(2))
	try:
		game = Commands.get_game(cid)
		uid = callback.from_user.id
		if not _claim_socialist_power(game, uid, "escucha"):
			bot.edit_message_text(t("soc.proposal_in_progress", game), uid, callback.message.message_id)
			return
		chosen = game.playerlist[answer]
		bot.edit_message_text(u"\U0001F41B" + t("soc.you_proposed_escucha", game) % chosen.name, uid, callback.message.message_id)
		_proponer_objetivo(bot, game, "escucha", uid, chosen)
	except Exception as e:
		log.error("choose_escucha: " + repr(e))
		log.exception(e)


def _aplicar_escucha(bot, game, chosen):
	log.info("Los socialistas escucharon a %s (%d): %s" % (chosen.name, chosen.uid, chosen.party))
	texto = u"\U0001F41B" + t("soc.escucha_result", game) % (chosen.name, party_name(chosen.party, game))
	_avisar_socialistas(bot, game, texto)
	bot.send_message(game.cid, t("soc.escucha_used_group", game))
	game.history.append(t("soc.escucha_used_history", game))
	game.hiddenhistory.append(t("soc.escucha_hidden", game) % (chosen.name, party_name(chosen.party, game)))
	start_next_round(bot, game)


def action_reclutamiento(bot, game):
	log.info('action_reclutamiento called')
	bot.send_message(game.cid,
		t("soc.reclutamiento_title", game) + u"\u270A" + t("soc.reclutamiento_body", game))
	_ofrecer_poder_socialista(bot, game, "reclutamiento")


def choose_reclutamiento(update: Update, context: CallbackContext):
	bot = context.bot
	callback = update.callback_query
	regex = re.search("(-[0-9]*)_socrec_(.*)", callback.data)
	cid = int(regex.group(1))
	answer = int(regex.group(2))
	try:
		game = Commands.get_game(cid)
		uid = callback.from_user.id
		if not _claim_socialist_power(game, uid, "reclutamiento"):
			bot.edit_message_text(t("soc.proposal_in_progress", game), uid, callback.message.message_id)
			return
		chosen = game.playerlist[answer]
		bot.edit_message_text(u"\u270A" + t("soc.you_proposed_reclutamiento", game) % chosen.name, uid, callback.message.message_id)
		_proponer_objetivo(bot, game, "reclutamiento", uid, chosen)
	except Exception as e:
		log.error("choose_reclutamiento: " + repr(e))
		log.exception(e)


def _aplicar_reclutamiento(bot, game, chosen):
	if not hasattr(game.board.state, "recruited_uids"):
		game.board.state.recruited_uids = []
	game.board.state.recruited_uids.append(chosen.uid)

	# El Reclutamiento cambia la carta de afiliacion, nunca el rol. A Hitler tambien le
	# cambia la carta (por eso una investigacion pasa a verlo socialista), pero para todo
	# lo demas sigue siendo fascista: no despierta con ellos ni gana con ellos. De eso se
	# encarga Player.party_efectiva(), no una excepcion aca.
	chosen.party = "socialista"
	chosen.was_recruited = True
	if chosen.role == "Hitler":
		# Los socialistas no se enteran del fracaso ahora, sino recien en el Congreso.
		log.info("Los socialistas intentaron reclutar a Hitler (%d)" % chosen.uid)
		bot.send_message(ADMIN if game.is_debugging else chosen.uid,
			u"\u270A" + t("soc.recruited_hitler_dm", game),
			parse_mode=ParseMode.MARKDOWN)
		game.hiddenhistory.append(t("soc.recruited_hitler_hidden", game) % chosen.name)
	else:
		log.info("Los socialistas reclutaron a %s (%d)" % (chosen.name, chosen.uid))
		bot.send_message(ADMIN if game.is_debugging else chosen.uid,
			u"\u270A" + t("soc.recruited_dm", game),
			parse_mode=ParseMode.MARKDOWN)
		game.hiddenhistory.append(t("soc.recruited_hidden", game) % chosen.name)

	_avisar_socialistas(bot, game, u"\u270A" + t("soc.recruitment_chosen", game) % chosen.name)
	bot.send_message(game.cid, t("soc.recruitment_used_group", game))
	game.history.append(t("soc.recruitment_used_history", game))
	start_next_round(bot, game)


def action_plan_quinquenal(bot, game):
	log.info('action_plan_quinquenal called')
	# Si quedan menos de 3 politicas hay que mezclar ANTES de agregar las nuevas.
	shuffle_policy_pile(bot, game)
	game.board.policies += ["socialista", "socialista", "liberal"]
	game.board.policies = random.sample(game.board.policies, len(game.board.policies))
	msg = (t("soc.plan_title", game) + u"\u0035\uFE0F\u20E3" +
		t("soc.plan_body", game) % len(game.board.policies))
	bot.send_message(game.cid, msg)
	game.history.append(msg)
	game.hiddenhistory.append(msg)
	start_next_round(bot, game)


def action_congreso(bot, game):
	log.info('action_congreso called')
	bot.send_message(game.cid,
		t("soc.congreso_title", game) + u"\U0001F3DB" + t("soc.congreso_body", game))
	originales = game.get_socialists()
	reclutados_uids = getattr(game.board.state, "recruited_uids", [])
	# Hitler no cuenta como socialista nuevo aunque tenga la carta: justamente por eso el
	# Congreso delata que el reclutado era el.
	nuevos = [game.playerlist[u] for u in reclutados_uids
		if u in game.playerlist and game.playerlist[u].party_efectiva() == "socialista"]

	nombres_originales = ", ".join(s.name for s in originales) or t("soc.nobody", game)
	for nuevo in nuevos:
		bot.send_message(ADMIN if game.is_debugging else nuevo.uid,
			u"\U0001F3DB" + t("soc.congreso_originals", game) % nombres_originales,
			parse_mode=ParseMode.MARKDOWN)

	if not reclutados_uids:
		aviso = u"\U0001F3DB" + t("soc.congreso_none_recruited", game)
	elif not nuevos:
		# El unico reclutado no se convirtio: era Hitler.
		aviso = u"\U0001F3DB" + t("soc.congreso_was_hitler", game)
	else:
		aviso = u"\U0001F3DB" + t("soc.congreso_new", game) % ", ".join(n.name for n in nuevos)
	for original in originales:
		if original.is_dead:
			continue
		bot.send_message(ADMIN if game.is_debugging else original.uid, aviso, parse_mode=ParseMode.MARKDOWN)
		if game.is_debugging:
			break
	game.history.append(t("soc.congreso_history", game))
	game.hiddenhistory.append(t("soc.congreso_hidden", game) % (
		nombres_originales, ", ".join(n.name for n in nuevos) or t("soc.none", game)))
	start_next_round(bot, game)


def action_confesion(bot, game):
	log.info('action_confesion called')
	presidente = game.board.state.president
	if presidente is None:
		# Puede pasar si la politica salio por anarquia: no hay presidente que confiese.
		bot.send_message(game.cid, t("soc.confesion_skip_title", game) + u"\U0001F4D6" + t("soc.confesion_skip_body", game))
		start_next_round(bot, game)
		return
	bot.send_message(game.cid,
		t("soc.confesion_title", game) + u"\U0001F4D6" + t("soc.confesion_body", game) % presidente.name)
	_ofrecer_poder_socialista(bot, game, "confesion")


def choose_confesion(update: Update, context: CallbackContext):
	bot = context.bot
	callback = update.callback_query
	regex = re.search("(-[0-9]*)_socconf_(.*)", callback.data)
	cid = int(regex.group(1))
	answer = int(regex.group(2))
	try:
		game = Commands.get_game(cid)
		uid = callback.from_user.id
		if not _claim_socialist_power(game, uid, "confesion"):
			bot.edit_message_text(t("soc.proposal_in_progress", game), uid, callback.message.message_id)
			return
		chosen = game.playerlist[answer]
		bot.edit_message_text(u"\U0001F4D6" + t("soc.you_proposed_confesion", game) % chosen.name,
			uid, callback.message.message_id)
		_proponer_objetivo(bot, game, "confesion", uid, chosen)
	except Exception as e:
		log.error("choose_confesion: " + repr(e))
		log.exception(e)


def _aplicar_confesion(bot, game, chosen):
	presidente = game.board.state.president
	log.info("Confesion: %s (%d) ve la afiliacion del presidente %s" % (chosen.name, chosen.uid, presidente.name))
	bot.send_message(ADMIN if game.is_debugging else chosen.uid,
		u"\U0001F4D6" + t("soc.confesion_result", game) % (presidente.name, party_name(presidente.party, game)),
		parse_mode=ParseMode.MARKDOWN)
	# La confesion se hace a la vista de todos: el grupo si se entera de quien la recibio.
	bot.send_message(game.cid,
		t("soc.confesion_announce", game) % (presidente.name, chosen.name))
	game.history.append(t("soc.confesion_announce", game) % (presidente.name, chosen.name))
	start_next_round(bot, game)


def start_next_round(bot, game):
    log.info('start_next_round called')
    # start next round if there is no winner (or /cancel)
    if game.board.state.game_endcode == 0:
        # start new round
        sleep(5)
        # if there is no special elected president in between
        if game.board.state.chosen_president is None:
            increment_player_counter(game)
        start_round(bot, game)


def decide_anarquia(bot, game):
	log.info('decide_anarquia called')
	#When voting starts we start the counter to see later with the vote command if we can see you voted.
	game.board.state.votes_anarquia = {}
	strcid = str(game.cid)
	btns = [[InlineKeyboardButton("Ja", callback_data=strcid + "_SiAna"),
	InlineKeyboardButton("Nein", callback_data=strcid + "_NoAna")]]
	voteMarkup = InlineKeyboardMarkup(btns)
	for uid in game.playerlist:
		if not game.is_debugging:
			if not game.playerlist[uid].is_dead:                      
				Commands.print_board(bot, game, uid)				
				bot.send_message(uid, t("anarchy.ask", game), reply_markup=voteMarkup)
		else:
			bot.send_message(ADMIN, game.board.print_board(game.player_sequence, game))
			bot.send_message(ADMIN, t("anarchy.ask", game), reply_markup=voteMarkup)
			
def handle_voting_anarquia(update: Update, context: CallbackContext):
	bot = context.bot
	callback = update.callback_query
	log.info('handle_voting_anarquia called: %s' % callback.data)
	regex = re.search("(-[0-9]*)_(.*)", callback.data)
	cid = int(regex.group(1))
	answer = regex.group(2)
	strcid = regex.group(1)
	try:
		game = Commands.get_game(cid)
		uid = callback.from_user.id
		answer = answer.replace("Ana", "")
		bot.edit_message_text(t("anarchy.vote_thanks", game) % (answer), uid, callback.message.message_id)
		log.info("Player %s (%d) voted %s" % (callback.from_user.first_name, uid, answer))

		#if uid not in game.board.state.last_votes:
		game.board.state.votes_anarquia[uid] = answer
		
		if game.is_debugging:
			for uid in game.playerlist:
				if not game.playerlist[uid].is_dead:
					game.board.state.votes_anarquia[uid] = answer			

		#Allow player to change his vote
		btns = [[InlineKeyboardButton("Ja", callback_data=strcid + "_JaAna"),
		InlineKeyboardButton("Nein", callback_data=strcid + "_NeinAna")]]
		voteMarkup = InlineKeyboardMarkup(btns)
		bot.send_message(uid, t("anarchy.change_ask", game), reply_markup=voteMarkup)
		
		if len(game.board.state.votes_anarquia) == len(game.player_sequence):
			count_votes_anarquia(bot, game)
		'''elif list(game.board.state.votes_anarquia.values()).count("Si") >= (len(game.player_sequence) / 2):
			# Caso especial si ya la mitad o mas de los jugadores decidio ir a anarquia se va no más.
			count_votes_anarquia(bot, game)
		'''
	except Exception as e:
		log.error(str(e))

def count_votes_anarquia(bot, game):
	# La votacion ha finalizado.
	game.dateinitvote = None
	# La votacion ha finalizado.
	log.info('count_votes_anarquia called')
	voting_text = ""
	voting_success = False
	for player in game.player_sequence:
		nombre_jugador = game.playerlist[player.uid].name
		if game.board.state.votes_anarquia[player.uid] == "Si":
			voting_text += nombre_jugador + t("vote.voted_ja_suffix", game)
		elif game.board.state.votes_anarquia[player.uid] == "No":
			voting_text += nombre_jugador + t("vote.voted_nein_suffix", game)
	if list(game.board.state.votes_anarquia.values()).count("Si") >= (len(game.player_sequence) / 2):  # because player_sequence doesnt include dead
		# VOTING WAS SUCCESSFUL
		log.info("Vamos a anarquia!")
		resultado_text = t("anarchy.approved", game)
		voting_text += resultado_text
		game.board.state.nominated_president = None
		game.board.state.nominated_chancellor = None
		bot.send_message(game.cid, voting_text, ParseMode.MARKDOWN)
		bot.send_message(game.cid, t("vote.no_talking", game))
		game.history.append(entrada_votacion(game, game.board.state.votes_anarquia, "Si", "No",
			t("history.round_header", game) % (politicas_promulgadas(game) + 1, game.board.state.failed_votes + 1),
			resultado_text, empate_pierde_ja=False))
		# Avanzo la cantidad del lider asi el lider queda correctamente asignado
		# Se incrementa como mucho 2 ya que el ultimo incremento lo hace la anarquia
		for i in range(2 - game.board.state.failed_votes):
			increment_player_counter(game)		
		do_anarchy(bot, game)
	else:
		log.info("La gente no quiere anarquia")
		resultado_text = t("anarchy.rejected", game)
		voting_text += resultado_text
		game.board.state.nominated_president = None
		game.board.state.nominated_chancellor = None
		bot.send_message(game.cid, voting_text, ParseMode.MARKDOWN)
		game.history.append(entrada_votacion(game, game.board.state.votes_anarquia, "Si", "No",
			t("history.round_header", game) % (politicas_promulgadas(game) + 1, game.board.state.failed_votes + 1),
			resultado_text, empate_pierde_ja=False))
		#game.board.state.failed_votes == 3
		
			
##
#
# End of round
#
##

def get_stats(bot, cid):
	conn = psycopg2.connect(
		database=url.path[1:],
		user=url.username,
		password=url.password,
		host=url.hostname,
		port=url.port
	)
	cur = conn.cursor()
	query = "select * from stats_secret_hitler"
	cur.execute(query)
	dbdata = cur.fetchone()
	conn.close()
	return dbdata
	

def set_stats(column_name, value, bot, cid):
	conn = psycopg2.connect(
		database=url.path[1:],
		user=url.username,
		password=url.password,
		host=url.hostname,
		port=url.port
	)
	try:
		cursor = conn.cursor()
		#cursor.execute("UPDATE stats SET %s=%s", (column_name, value));		
		cursor.execute(sql.SQL("UPDATE stats_secret_hitler set {}=%s ").format(sql.Identifier(column_name)), [value])
		
		conn.commit()
	except Exception as e:
		bot.send_message(cid, t("error.set_stats_failed", cid)+str(e))
		conn.rollback()
	conn.close()
		
def save_game_details(bot, print_roles, game_endcode, liberal_track, fascist_track, num_players):
	conn = psycopg2.connect(
		database=url.path[1:],
		user=url.username,
		password=url.password,
		host=url.hostname,
		port=url.port
	)
	#Check if game is in DB first
	cursor = conn.cursor()			
	log.info("Executing in DB")		
	query = "INSERT INTO stats_detail_secret_hitler(playerlist, game_endcode, liberal_track, fascist_track, num_players) VALUES (%s, %s, %s, %s, %s);"
	#query = "INSERT INTO games(id , groupName  , data) VALUES (%s, %s, %s) RETURNING data;"
	cursor.execute(query, (print_roles, game_endcode, liberal_track, fascist_track, num_players))		
	#dbdata = cur.fetchone()
	conn.commit()
	conn.close()
	

def change_stats(uid, tipo_juego, stat_name, amount):
	user_stats = load_player_stats(uid)		
	# Si no tiene registro, lo creo
	if user_stats is None:
		user_stats = PlayerStats(uid)	
	user_stats.change_data_stat(tipo_juego, stat_name, amount)
	save_player_stats(uid, user_stats)	

def save_player_stats(uid, data):
	conn = psycopg2.connect(
		database=url.path[1:],
		user=url.username,
		password=url.password,
		host=url.hostname,
		port=url.port
	)
	#Check if game is in DB first
	cur = conn.cursor()			
	log.info("Searching Game in DB")
	query = "select * from user_stats where id = %s;"
	cur.execute(query, [uid])
	#dbdata = cur.fetchone()
	if cur.rowcount > 0:
		log.info('Updating user_stats')
		datajson = jsonpickle.encode(data)
		#query = "UPDATE games_secret_hitler SET groupName = %s, data = %s WHERE id = %s RETURNING data;"
		query = "UPDATE user_stats SET data = %s WHERE id = %s;"
		cur.execute(query, (datajson, uid))
		#log.info(cur.fetchone()[0])
		conn.commit()		
	else:
		log.info('Saving user_stats in DB')
		datajson = jsonpickle.encode(data)
		query = "INSERT INTO user_stats(id, data) VALUES (%s, %s);"
		#query = "INSERT INTO games(id , groupName  , data) VALUES (%s, %s, %s) RETURNING data;"
		cur.execute(query, (uid, datajson))
		#log.info(cur.fetchone()[0])
		conn.commit()
	conn.close()

def load_player_stats(uid):
	conn = psycopg2.connect(
		database=url.path[1:],
		user=url.username,
		password=url.password,
		host=url.hostname,
		port=url.port
	)
	cur = conn.cursor()			
	log.info("Searching Game in DB")
	query = "SELECT * FROM user_stats WHERE id = %s;"
	cur.execute(query, [uid])
	dbdata = cur.fetchone()

	if cur.rowcount > 0:
		log.info("user_stats Found")
		jsdata = dbdata[1]
		log.info("jsdata = {}".format(jsdata))				
		stats = jsonpickle.decode(jsdata)
		conn.close()
		return stats
	else:
		log.info("user_stats Not Found")
		conn.close()
		return None
	

##
# game_endcode:
#   -2  fascists win by electing Hitler as chancellor
#   -1  fascists win with 6 fascist policies
#   0   not ended
#   1   liberals win with 5 liberal policies
#   2   liberals win by killing Hitler
#   3   socialists win with their whole socialist track (solo modo socialista)
#   99  game cancelled
#
def end_game(bot, game, game_endcode):
	log.info('end_game called')
	cid = game.cid
	# Partida de prueba (/prueba): termina y se revela igual que cualquier otra, pero sin
	# guardar ninguna estadistica, sin evaluar logros y sin votacion de MVP.
	es_prueba = game.es_prueba()
	
	# Grabo detalles de la partida
	nuevos_logros = {}
	game.stats_game_id = None
	if game_endcode != 99 and not es_prueba:
		# "es" a proposito: las consultas de /stats buscan este texto con LIKE en espanol.
		save_game_details(bot, game.print_roles("es"), game_endcode, game.board.state.liberal_track, game.board.state.fascist_track, game.board.num_players)
		nuevos_logros, game.stats_game_id = StatsExtended.save_extended_game_stats(game, game_endcode)


	#bot.send_message(cid, "Datos a guardar %s %s %s %s %s" % (game.print_roles(), str(game_endcode), str(game.board.state.liberal_track), str(game.board.state.fascist_track), str(game.board.num_players)))
		
	stats = get_stats(bot, cid)	

	def contar_stat(column_name, value):
		# En una partida de prueba no se suma nada a las estadisticas del grupo.
		if not es_prueba:
			set_stats(column_name, value, bot, cid)

	if game_endcode == 99:
		if GamesController.games[cid].board is not None:
			bot.send_message(cid, t("end.cancelled_with_roles", game) % game.print_roles(game))
		else:
			bot.send_message(cid, t("end.cancelled", game))
		contar_stat("cancelgame", stats[5] + 1)
	else:
		if game_endcode == -2:
			bot.send_message(game.cid, t("end.fascists_win_hitler", game) % game.print_roles(game))
			contar_stat("fascistwinhitler", stats[1] + 1)
		if game_endcode == -1:
			bot.send_message(game.cid, t("end.fascists_win_policies", game) % game.print_roles(game))
			contar_stat("fascistwinpolicies", stats[2] + 1)
		if game_endcode == 1:
			bot.send_message(game.cid, t("end.liberals_win_policies", game) % game.print_roles(game))
			contar_stat("liberalwinpolicies", stats[3] + 1)
		if game_endcode == 2:
			bot.send_message(game.cid, t("end.liberals_win_kill", game) % game.print_roles(game))
			contar_stat("liberalwinkillhitler", stats[4] + 1)
		if game_endcode == 3:
			bot.send_message(game.cid, t("end.socialists_win", game) % game.print_roles(game))
			# La columna es nueva (la agrega DBCreate.sql), asi que puede no existir en bases viejas.
			if len(stats) > 6:
				contar_stat("socialistwinpolicies", stats[6] + 1)
		try:
			reveal = Commands.format_guesses_reveal(game)
			if reveal is not None:
				Commands.send_chunked_message(bot, cid, reveal, parse_mode=ParseMode.MARKDOWN)
		except Exception as e:
			log.error("No se pudo mostrar los resultados de las adivinanzas: %s" % str(e))
		showHiddenhistory(bot, game)
		try:
			anuncio = Achievements.format_unlock_announcement(nuevos_logros, game)
			if anuncio is not None:
				bot.send_message(cid, anuncio, ParseMode.MARKDOWN)
		except Exception as e:
			log.error("No se pudo anunciar los logros nuevos: %s" % str(e))
		if es_prueba:
			bot.send_message(cid,
				t("end.prueba_notice", game),
				ParseMode.MARKDOWN)
		else:
			bot.send_message(cid,
				t("end.mvp_invite", game))

	if game_endcode == 99 or es_prueba:
		# Nada que esperar: sin estadisticas ni votacion de MVP, la partida se borra ya.
		if cid in GamesController.games:
			del GamesController.games[cid]
		Commands.delete_game(cid)
	else:
		# La partida sigue viva (en memoria y en BD) hasta que todos voten su /mvp;
		# recien ahi callback_mvp_vote la termina de borrar.
		Commands.save_game(cid, game.groupName, game)
	
def showHiddenhistory(bot, game):	
	#game.pedrote = 3
	try:
		# Obtengo las politicas que quedaron en el mazo	
		remaining_policies = t("hidden.remaining_policies", game)		
		for i in range(len(game.board.policies)):
			remaining_policies += policy_name(game.board.policies[i], game) + "\n"
		# Se comienza a obtener el historial oculto
		history_text = t("hidden.title", game) 
		for x in game.hiddenhistory:				
			history_text += x + "\n"
		bot.send_message(game.cid, history_text + remaining_policies, ParseMode.MARKDOWN)
	except Exception as e:
		bot.send_message(game.cid, str(e))
		log.error("Unknown error: " + str(e)) 
        
def inform_players(bot, game, cid, player_number):
	log.info('inform_players called')
	bot.send_message(cid,
		t("start.begin_game", game) % (
		player_number, print_player_info(game, player_number)))
	available_roles = list(get_role_set(game, player_number))  # copy not reference because we need it again later
	# Mezclo los roles asi si alguien elije Fascista o Hitler no le toca siempre Fascista
	random.shuffle(available_roles)
	# Creo una lista unica para poder repartir los roles a partir de las key de los player list
	player_ids = list(game.playerlist.keys())
	# Lo mezclo y lo uso para pasar por todos los jugadores
	random.shuffle(player_ids)
	
	for uid in player_ids:
		# Antes de buscar un rol en particular pregunto si el jugador queria ser algo en particular
		preferencia_jugador = game.playerlist[uid].preference_rol		
		# Si el jugador tiene una preferencia... defecto se pone "" y daria [''] como preferencias		
		preferencias = preferencia_jugador.split('_')
		# El primer rol que aparece de las preferencias del jugador, devuelve None si no hay
		indice_preferencia = next((i for i,v in enumerate(available_roles) if v in preferencias), -1)
		
		# Si el jugador tiene una preferencia se le asigna esta, como el orden es random no se sabe si se sabe si se
		# cumplirá esto ya que los roles pudieron haber sido tomados ya.		
		if indice_preferencia == -1:
			#print "No hay indices de la preferencia"
			random_index = random.randrange(len(available_roles))
		else:
			random_index = indice_preferencia
			
		#log.info(str(random_index))
		role = available_roles.pop(random_index)
		#log.info(str(role))
		party = get_membership(role)
		game.playerlist[uid].role = role
		game.playerlist[uid].party = party

	# Recien aca, con los roles de TODOS los jugadores ya asignados (get_private_info necesita
	# poder consultar game.get_fascists()/game.get_hitler() completos), mando un unico mensaje
	# por jugador con toda su info y lo pinneo en su chat privado con el bot.
	for uid in player_ids:
		# I comment so tyhe player aren't discturbed in testing, uncomment when deploy to production
		if not game.is_debugging:
			msg = game.playerlist[uid].get_private_info(game)
			sent = bot.send_message(uid, msg, parse_mode=ParseMode.MARKDOWN)
			try:
				bot.pin_chat_message(uid, sent.message_id, disable_notification=True)
			except Exception as e:
				log.error("No se pudo pinnear el mensaje de rol de %s: %s" % (game.playerlist[uid].name, str(e)))
		else:
			bot.send_message(ADMIN, "El jugador %s es %s y su afiliación política es: %s" % (
				game.playerlist[uid].name, role_name(game.playerlist[uid].role, game), party_name(game.playerlist[uid].party, game)))


def get_role_set(game, player_number):
    # El reparto de roles depende del modo: la expansion socialista tiene su propia tabla
    # (6 a 13 jugadores) y agrega el rol Socialista.
    if game.es_socialista():
        return list(socialistSets[player_number]["roles"])
    return list(playerSets[player_number]["roles"])


def print_player_info(game, player_number):
    if game.es_socialista():
        roles = socialistSets[player_number]["roles"]
        return (t("setup.roles_socialista", game) % (
            roles.count("Liberal"), roles.count("Fascista"), roles.count("Socialista")))
    if player_number == 5:
        return t("setup.roles_5", game)
    elif player_number == 6:
        return t("setup.roles_6", game)
    elif player_number == 7:
        return t("setup.roles_7", game)
    elif player_number == 8:
        return t("setup.roles_8", game)
    elif player_number == 9:
        return t("setup.roles_9", game)
    elif player_number == 10:
        return t("setup.roles_10", game)


def get_membership(role):
    log.info('get_membership called')
    if role == "Fascista" or role == "Hitler":
        return "fascista"
    elif role == "Liberal":
        return "liberal"
    elif role == "Socialista":
        return "socialista"
    else:
        return None


def increment_player_counter(game):
    log.info('increment_player_counter called')
    if game.board.state.player_counter < len(game.player_sequence) - 1:
        game.board.state.player_counter += 1
    else:
        game.board.state.player_counter = 0


def shuffle_policy_pile(bot, game):
	log.info('shuffle_policy_pile called')
	if len(game.board.policies) < 3:
		game.history.append(t("shuffle.history", game))
		game.hiddenhistory.append(t("shuffle.history", game))
		game.board.discards += game.board.policies
		game.board.policies = random.sample(game.board.discards, len(game.board.discards))
		game.board.discards = []		
		bot.send_message(game.cid,
			t("shuffle.announce", game))
		# Buen momento para recordar /guess: ya hubo varias rondas para formarse una idea.
		bot.send_message(game.cid, t("shuffle.guess_reminder", game))

def getGamesByTipo(opcion):
	conn = psycopg2.connect(
		database=url.path[1:],
		user=url.username,
		password=url.password,
		host=url.hostname,
		port=url.port
	)
	games = None
	cursor = conn.cursor()			
	log.info("Executing in DB")
	if opcion != "Todos":
		query = "select * from games_secret_hitler g where g.tipojuego = '{0}'".format(opcion)
	else:
		query = "select * from games_secret_hitler g"
	
	cursor.execute(query)
	if cursor.rowcount > 0:
		# Si encuentro juegos los busco a todos y los cargo en memoria
		for table in cursor.fetchall():
			if table[0] not in GamesController.games.keys():
				Commands.get_game(table[0])
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

def error_callback(update, context):
	# add all the dev user_ids in this list. You can also add ids of channels or groups.
	devs = [ADMIN]    
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
	logger.warning("User: {}.\n\nError {}.\n\nTrace: {}".format(update.effective_user.first_name, context.error, trace))
	
def change_groupname(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat.id
	groupname = update.message.chat.title
	game = Commands.get_game(cid)
	if game is not None:
		game.groupName = groupname
		Commands.save_game(cid, game.groupName, game)
	bot.send_message(ADMIN, text="El grupo en {cid} ha cambiado de nombre a {groupname}".format(groupname=groupname, cid=cid))

def track_new_members(update: Update, context: CallbackContext):
	cid = update.message.chat.id
	for member in update.message.new_chat_members:
		GroupMembers.upsert_member(cid, member.id, member.first_name.replace("_", " "), is_bot=member.is_bot, active=True)

def track_left_member(update: Update, context: CallbackContext):
	cid = update.message.chat.id
	member = update.message.left_chat_member
	GroupMembers.upsert_member(cid, member.id, member.first_name.replace("_", " "), is_bot=member.is_bot, active=False)

def command_all(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	groupType = update.message.chat.type
	if groupType not in ['group', 'supergroup']:
		bot.send_message(cid, t("cmd.all.group_only", cid))
		return
	miembros = GroupMembers.get_active_members(cid)
	if not miembros:
		bot.send_message(cid, t("cmd.all.no_members", cid))
		return
	menciones = ["[{}](tg://user?id={})".format(name, uid) for uid, name in miembros]
	texto = t("cmd.all.header", cid) + "\n".join(menciones)
	Commands.send_chunked_message(bot, cid, texto, parse_mode=ParseMode.MARKDOWN)

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
	conn.close()
	return token

# Tablas que DBCreate.sql deberia mantener creadas. Se usa solo para el aviso de estado al arrancar.
SECRET_HITLER_TABLES = [
	"users",
	"games_secret_hitler",
	"stats_secret_hitler",
	"stats_detail_secret_hitler",
	"config",
	"user_stats",
	"achivements_secret_hitler",
	"stats_secret_hitler_games",
	"stats_secret_hitler_players",
	"achievements_secret_hitler_players",
	"language_secret_hitler",
	"history_mode_secret_hitler",
]

def _existing_tables(cur, table_names):
	cur.execute(
		"SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name = ANY(%s);",
		(table_names,)
	)
	return {row[0] for row in cur.fetchall()}

def init_db():
	# Corre DBCreate.sql (crea las tablas que falten) y devuelve un texto con el resultado
	# para avisarle al admin al arrancar. Nunca deja que un fallo aca tumbe el arranque del bot.
	conn = psycopg2.connect(
		database=url.path[1:],
		user=url.username,
		password=url.password,
		host=url.hostname,
		port=url.port
	)
	conn.autocommit = True
	cur = conn.cursor()

	tables_before = _existing_tables(cur, SECRET_HITLER_TABLES)

	log.info('Init DB Secret Hitler')
	db_init_error = None
	try:
		# Ruta absoluta: "DBCreate.sql" a secas se resuelve contra el cwd del proceso
		# (Main.py corre con cwd "/"), no contra esta carpeta, y terminaba leyendo
		# /DBCreate.sql (el del bot principal) en vez de SecretHitler/DBCreate.sql.
		sql_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "DBCreate.sql")
		cur.execute(open(sql_path, "r").read())
		log.info('DB Created/Updated Secret Hitler')
	except Exception as e:
		db_init_error = str(e)
		log.error("DBCreate.sql failed: %s" % db_init_error)

	tables_after = _existing_tables(cur, SECRET_HITLER_TABLES)
	conn.autocommit = False
	conn.close()

	created_now = sorted((set(SECRET_HITLER_TABLES) - tables_before) & tables_after)
	still_missing = sorted(set(SECRET_HITLER_TABLES) - tables_after)

	if db_init_error:
		return "No se pudieron verificar/crear las tablas (error: %s)." % db_init_error
	if still_missing:
		return "ATENCION: faltan estas tablas y no se pudieron crear: %s" % ", ".join(still_missing)
	if created_now:
		return "Se crearon las tablas faltantes: %s" % ", ".join(created_now)
	return "Todas las tablas de la base de datos ya existian."

# Comandos que aparecen en el menu "/" de Telegram, en orden. La descripcion de cada
# uno sale del catalogo de idioma (clave menu.<comando>), asi que agregar o sacar un
# comando de aca implica agregar o sacar esa clave en todos los idiomas.
MENU_COMANDOS = [
	"help", "start", "rules", "explainsocialista", "symbols", "roles", "language",
	"newgame", "nextgame", "join", "startgame", "board", "history", "votes",
	"calltovote", "retirar", "startautoja", "stopautoja", "conflicto", "info",
	"jugadores", "leave", "stats", "stats2", "logros", "guess", "mvp", "end",
	"prueba", "guessresults", "miguess", "version", "all",
]


def _menu_comandos(lang):
	return [BotCommand(comando, t("menu.%s" % comando, lang)) for comando in MENU_COMANDOS]


def main():
	GamesController.init() #Call only once
	db_status_text = init_db()
	# Precarga el idioma de cada chat para no consultar la base en cada mensaje.
	i18n.init()
	# Igual con el modo de /history de cada jugador (despues de init_db, que crea la tabla).
	HistoryPrefs.init()

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

	# polling
	'''
	updater = Updater(get_TOKEN())
	'''
	# Pruebas de HOOKS
	token = os.environ.get('TOKEN_SECRETHITLER', None)
	PORT = int(os.environ.get('PORT', '8443'))
	updater = Updater(token, use_context=True)
	
	# Lo de abajo se usa para web deploy son web hooks
	'''
	updater.start_webhook(listen="0.0.0.0",
                      port=PORT,
                      url_path=token)
	updater.bot.set_webhook("https://secrethitler.herokuapp.com/{0}".format(token))
	'''
	
	# Get the dispatcher to register handlers
	dp = updater.dispatcher

	# on different commands - answer in Telegram
	dp.add_handler(CommandHandler("start", Commands.command_start))
	dp.add_handler(CommandHandler("help", Commands.command_help))
	dp.add_handler(CommandHandler("board", Commands.command_board))
	dp.add_handler(CommandHandler("rules", Commands.command_rules))
	dp.add_handler(CommandHandler("explainsocialista", Commands.command_explainsocialista))
	dp.add_handler(CommandHandler("ping", Commands.command_ping))
	dp.add_handler(CommandHandler("version", Commands.command_version))
	dp.add_handler(CommandHandler("language", Commands.command_language))
	dp.add_handler(CommandHandler("idioma", Commands.command_language))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*chooseLanguage\*(.*)\*(-?[0-9]*)", callback=Commands.callback_language))
	dp.add_handler(CommandHandler("symbols", Commands.command_symbols))
	dp.add_handler(CommandHandler("roles", Commands.command_roles))
	dp.add_handler(CommandHandler("stats", Commands.command_stats))
	dp.add_handler(CommandHandler("stats2", Commands.command_stats2))
	dp.add_handler(CommandHandler("logros", Commands.command_logros))
	dp.add_handler(CommandHandler("guess", Commands.command_guess))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*chooseGameGuess\*(.*)\*(-?[0-9]*)", callback=Commands.callback_guess_game))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)_guessf_(-?[0-9]*)", callback=Commands.callback_guess_fascist))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)_guessh_(-?[0-9]*)", callback=Commands.callback_guess_hitler))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)_guesspred_(-?[0-9]*)", callback=Commands.callback_guess_prediction))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)_guesssoc_(-?[0-9]*)", callback=Commands.callback_guess_socialist))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)_guessskip_([a-z]+)", callback=Commands.callback_guess_skip))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)_guessconfirm", callback=Commands.callback_guess_confirm))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)_guessrestart", callback=Commands.callback_guess_restart))
	dp.add_handler(CommandHandler("mvp", Commands.command_mvp))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*chooseGameMvp\*(.*)\*(-?[0-9]*)", callback=Commands.callback_mvp_game))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)_mvpvote_(-?[0-9]*)", callback=Commands.callback_mvp_vote))
	dp.add_handler(CommandHandler("end", Commands.command_end))
	dp.add_handler(CommandHandler("prueba", Commands.command_prueba))
	dp.add_handler(CommandHandler("guessresults", Commands.command_guessresults))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*chooseGameGuessResults\*(.*)\*(-?[0-9]*)", callback=Commands.callback_guessresults_game))
	dp.add_handler(CommandHandler("miguess", Commands.command_miguess))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*chooseGameMiguess\*(.*)\*(-?[0-9]*)", callback=Commands.callback_miguess_game))
	dp.add_handler(CommandHandler("vincularstats", Commands.command_vincularstats))
	dp.add_handler(CommandHandler("vincularstats2", Commands.command_vincularstats2))
	dp.add_handler(CommandHandler("admin", Commands.command_admin))
	dp.add_handler(CallbackQueryHandler(pattern=r"^admin_games$", callback=Commands.callback_admin_games))
	dp.add_handler(CallbackQueryHandler(pattern=r"^admin_menu$", callback=Commands.callback_admin_menu))
	dp.add_handler(CallbackQueryHandler(pattern=r"^admin_game_-?[0-9]+$", callback=Commands.callback_admin_game))
	dp.add_handler(CallbackQueryHandler(pattern=r"^admin_del(ask|yes)_-?[0-9]+$", callback=Commands.callback_admin_delete))
	dp.add_handler(CallbackQueryHandler(pattern=r"^admin_first$", callback=Commands.callback_admin_first))
	dp.add_handler(CallbackQueryHandler(pattern=r"^admin_cleanup_mision$", callback=Commands.callback_admin_cleanup_mision))
	dp.add_handler(CommandHandler("newgame", Commands.command_newgame))
	dp.add_handler(CommandHandler("startgame", Commands.command_startgame))
	dp.add_handler(CommandHandler("cancelgame", Commands.command_cancelgame))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*confirmCancel\*(si|no)\*(-?[0-9]*)", callback=Commands.callback_cancelgame_confirm))
	dp.add_handler(CommandHandler("join", Commands.command_join))
	dp.add_handler(CommandHandler("history", Commands.command_showhistory))
	dp.add_handler(CommandHandler("votes", Commands.command_votes))
	dp.add_handler(CommandHandler("calltovote", Commands.command_calltovote))
	dp.add_handler(CommandHandler("retirar", Commands.command_retract_vote))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*chooseGameRetract\*(.*)\*(-?[0-9]*)", callback=Commands.callback_retract))
	dp.add_handler(CommandHandler("startautoja", Commands.command_startautoja))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*chooseGameStartAutoJa\*(.*)\*(-?[0-9]*)", callback=Commands.callback_startautoja))
	dp.add_handler(CommandHandler("stopautoja", Commands.command_stopautoja))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*chooseGameStopAutoJa\*(.*)\*(-?[0-9]*)", callback=Commands.callback_stopautoja))
	dp.add_handler(CommandHandler("conflicto", Commands.command_conflicto))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*autojacorte\*(.*)\*(-?[0-9]*)", callback=Commands.callback_autoja_corte))
	dp.add_handler(CommandHandler("claim", Commands.command_claim))
	dp.add_handler(CommandHandler("reload", Commands.command_reloadgame))
	dp.add_handler(CommandHandler("debug", Commands.command_toggle_debugging))
	dp.add_handler(CommandHandler("anarchy", Commands.command_anarquia))
	dp.add_handler(CommandHandler("fix", Commands.command_fix))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*chooseGameFix\*(.*)\*(-?[0-9]*)", callback=Commands.callback_fix))
	dp.add_handler(CommandHandler("fix2", Commands.command_fix2))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*chooseGameFix2\*(.*)\*(-?[0-9]*)", callback=Commands.callback_fix2_game))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)_fix2chan_(.*)", callback=Commands.callback_fix2_chancellor))
	dp.add_handler(CommandHandler("fix3", Commands.command_fix3))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*chooseGameFix3\*(.*)\*(-?[0-9]*)", callback=Commands.callback_fix3_game))
	dp.add_handler(CommandHandler("fix4", Commands.command_fix4))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*chooseGameFix4\*(.*)\*(-?[0-9]*)", callback=Commands.callback_fix4_game))
	dp.add_handler(CommandHandler("fix5", Commands.command_fix5))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*chooseGameFix5\*(.*)\*(-?[0-9]*)", callback=Commands.callback_fix5_game))
	dp.add_handler(CommandHandler("fix6", Commands.command_fix6))
	dp.add_handler(CommandHandler("claimoculto", Commands.command_claim_oculto))
	dp.add_handler(CommandHandler("info", Commands.command_info))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*chooseGameInfo\*(.*)\*(-?[0-9]*)", callback=Commands.callback_info))
	dp.add_handler(CommandHandler("jugadores", Commands.command_jugadores))
	dp.add_handler(CommandHandler("leave", Commands.command_leave))
	dp.add_handler(CommandHandler("setpresidente", Commands.command_player_counter))
	dp.add_handler(CommandHandler("stad", Commands.command_print_stad))
	#Testing commands
	dp.add_handler(CommandHandler("ja", Commands.command_ja))
	dp.add_handler(CommandHandler("nein", Commands.command_nein))

	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_chan_(.*)", callback=nominate_chosen_chancellor))
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_chair_(.*)", callback=choose_chosen_chairman))
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_insp_(.*)", callback=choose_inspect))
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_choo_(.*)", callback=choose_choose))
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_kill_(.*)", callback=choose_kill))
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_socbug_(.*)", callback=choose_escucha))
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_socrec_(.*)", callback=choose_reclutamiento))
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_socconf_(.*)", callback=choose_confesion))
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_socvoto_(si|no)", callback=handle_socialist_vote))
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_(yesveto|noveto)", callback=choose_veto))
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_(liberal|fascista|socialista|veto)", callback=choose_policy))
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_(Ja|Nein)", callback=handle_voting))
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_(SiAna|NoAna)", callback=handle_voting_anarquia))
	
	dp.add_handler(CommandHandler("comando", Commands.command_newgame_sql_command))
	
	# Comandos para elegir rol al unirse a la partida
	dp.add_handler(CommandHandler("role", Commands.command_choose_posible_role))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*chooserole\*(.*)\*([0-9]*)", callback=Commands.callback_choose_posible_role))

	dp.add_handler(CommandHandler("showstats", Commands.command_show_stats))
	dp.add_handler(CommandHandler("changestats", Commands.command_change_stats))

	dp.add_handler(CommandHandler("status", command_status))

	dp.add_handler(MessageHandler(Filters.status_update.new_chat_title, change_groupname))
	dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, track_new_members))
	dp.add_handler(MessageHandler(Filters.status_update.left_chat_member, track_left_member))
	dp.add_handler(CommandHandler("all", command_all))
	dp.add_handler(CommandHandler("nextgame", Commands.command_nextgame))
	dp.add_handler(MessageHandler(Filters.text, command_status))

	# log all errors
	dp.add_error_handler(error_callback)

	# Registrar el menu de comandos que Telegram muestra al escribir "/". Se registra uno
	# por idioma: Telegram le muestra a cada usuario el que coincide con el idioma de su
	# cliente, y el español queda como default para todos los demás.
	try:
		updater.bot.set_my_commands(_menu_comandos(i18n.IDIOMA_DEFAULT))
	except Exception as e:
		log.error(str(e))
	for codigo in i18n.CATALOGOS:
		if codigo == i18n.IDIOMA_DEFAULT:
			continue
		try:
			updater.bot.set_my_commands(_menu_comandos(codigo), language_code=codigo)
		except Exception as e:
			log.error("set_my_commands(%s): %s" % (codigo, str(e)))

	updater.bot.send_message(ADMIN, "Nueva version en linea: v%s\n%s" % (VERSION, db_status_text))

	# Comentar linea de abajo si se quiere usar web deploy
	updater.start_polling(timeout=30)
	
	# pruebas de hooks
	updater.idle()
	
	'''
	# Start the Bot
	updater.start_polling()
	# Run the bot until the you presses Ctrl-C or the process receives SIGINT,
	# SIGTERM or SIGABRT. This should be used most of the time, since
	# start_polling() is non-blocking and will stop the bot gracefully.
	updater.idle()
	'''



if __name__ == '__main__':
    main()
