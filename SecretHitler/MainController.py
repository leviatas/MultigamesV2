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
from SecretHitler.Constants.Config import ADMIN, VERSION
from SecretHitler.Boardgamebox.Game import Game
from SecretHitler.Boardgamebox.Player import Player
from SecretHitler.PlayerStats import PlayerStats
import SecretHitler.GamesController as GamesController
import SecretHitler.StatsExtended as StatsExtended
import SecretHitler.Achievements as Achievements
import SecretHitler.GroupMembers as GroupMembers

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
	msgtext =  "El próximo candidato a presidente es [%s](tg://user?id=%d).\n%s, por favor nomina a un canciller en nuestro chat privado!" % (game.board.state.nominated_president.name, game.board.state.nominated_president.uid, game.board.state.nominated_president.name)
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
		bot.send_message(ADMIN, 'Por favor nomina a tu canciller!', parse_mode=ParseMode.MARKDOWN, reply_markup=chancellorMarkup)      
	else:
		Commands.print_board(bot, game, game.board.state.nominated_president.uid)
		groupName = ""
		if hasattr(game, 'groupName'):
			groupName += "*En el grupo {}*\n".format(game.groupName)
		msg = '{}Por favor nomina a tu canciller!'.format(groupName)
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
			bot.edit_message_text("No eres el presidente actual, no puedes nominar!", callback.from_user.id, callback.message.message_id)
			return

		game.board.state.nominated_chancellor = game.playerlist[chosen_uid]
		log.info("El Presidente %s (%d) nominó a %s (%d)" % (
					game.board.state.nominated_president.name, game.board.state.nominated_president.uid,
					game.board.state.nominated_chancellor.name, game.board.state.nominated_chancellor.uid))
		bot.edit_message_text("Tú nominaste a %s como canciller!" % game.board.state.nominated_chancellor.name,
					callback.from_user.id, callback.message.message_id)
		bot.send_message(game.cid,
					"El presidente %s nominó a %s como canciller. Por favor, vota ahora!" % (
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

def vote(bot, game):
	log.info('vote called')
	#When voting starts we start the counter to see later with the vote command if we can see you voted.
	game.dateinitvote = datetime.datetime.now()

	strcid = str(game.cid)
	btns = [[InlineKeyboardButton("Ja", callback_data=strcid + "_Ja"),
	InlineKeyboardButton("Nein", callback_data=strcid + "_Nein")]]
	voteMarkup = InlineKeyboardMarkup(btns)
	zona_hitler = is_zona_hitler(game)
	for uid in game.playerlist:
		if not game.playerlist[uid].is_dead and not game.is_debugging:
			if game.playerlist[uid] is not game.board.state.nominated_president:
				# the nominated president already got the board before nominating a chancellor
				Commands.print_board(bot, game, uid)
			groupName = ""
			if hasattr(game, 'groupName'):
				groupName += "*En el grupo {}*\n".format(game.groupName)
			msg = "{}Quieres elegir al Presidente *{}* y al canciller *{}*?".format(groupName, game.board.state.nominated_president.name, game.board.state.nominated_chancellor.name)
			if getattr(game.playerlist[uid], 'auto_ja', False) and not zona_hitler:
				game.board.state.last_votes[uid] = "Ja"
				msg += "\n\nTienes */startautoja* activado: tu voto *Ja* ya fue registrado automáticamente. Usa /retirar si querés votar distinto."
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
			bot.edit_message_text("No es el momento de votar!", uid, callback.message.message_id)
			return

		bot.edit_message_text("Gracias por tu voto: %s para el Presidente %s y el canciller %s" % (
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
			groupName += "*En el grupo {}*\n".format(game.groupName)

		msg = "{}\nPuedes cambiar tu voto aquí.\nQuieres elegir al Presidente *{}* y al canciller *{}*?".format(groupName, game.board.state.nominated_president.name, game.board.state.nominated_chancellor.name)
		bot.send_message(uid, msg, reply_markup=voteMarkup, parse_mode=ParseMode.MARKDOWN)
		Commands.save_game(game.cid, "vote Round %d" % (game.board.state.currentround), game)
		if len(game.board.state.last_votes) == len(game.player_sequence):
			count_votes(bot, game)
	except Exception as e:
		log.error(str(e))

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
			voting_text += nombre_jugador + " votó Ja!\n"
		elif game.board.state.last_votes[player.uid] == "Nein":
			voting_text += nombre_jugador + " votó Nein!\n"
	if list(game.board.state.last_votes.values()).count("Ja") > (
		len(game.player_sequence) / 2):  # because player_sequence doesnt include dead
		# VOTING WAS SUCCESSFUL
		log.info("Voting successful")
		voting_text += "Hail Presidente [%s](tg://user?id=%d)! Hail Canciller [%s](tg://user?id=%d)!" % (
			game.board.state.nominated_president.name, game.board.state.nominated_president.uid, 
				game.board.state.nominated_chancellor.name, game.board.state.nominated_chancellor.uid)
		game.board.state.chancellor = game.board.state.nominated_chancellor
		game.board.state.president = game.board.state.nominated_president
		game.board.state.nominated_president = None
		game.board.state.nominated_chancellor = None
		voting_success = True
		
		bot.send_message(game.cid, voting_text, ParseMode.MARKDOWN)
		bot.send_message(game.cid, "\nNo se puede hablar ahora.")
		game.history.append(("Ronda %d.%d\n\n" % (game.board.state.liberal_track + game.board.state.fascist_track + 1, game.board.state.failed_votes + 1) ) + voting_text)
		#log.info(game.history[game.board.state.currentround])
		voting_aftermath(bot, game, voting_success)
	else:
		log.info("Voting failed")
		voting_text += "Al pueblo no le gusto el Presidente %s y el canciller %s!" % (
			game.board.state.nominated_president.name, game.board.state.nominated_chancellor.name)
		game.board.state.nominated_president = None
		game.board.state.nominated_chancellor = None
		game.board.state.failed_votes += 1
		bot.send_message(game.cid, voting_text)
		game.history.append(("Ronda %d.%d\n\n" % (game.board.state.liberal_track + game.board.state.fascist_track + 1, game.board.state.failed_votes) ) + voting_text)
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
		bot.send_message(game.cid, "No hay ningún jugador disponible para ser Presidente de la Cámara, se pasa directo a la sesión legislativa.")
		draw_policies(bot, game)
		return

	chairmanMarkup = InlineKeyboardMarkup(btns)
	bot.send_message(game.cid,
		"El Canciller %s tiene que elegir al Presidente de la Cámara " % game.board.state.chancellor.name + u"\U0001F3DB")
	msg = 'Elegí al Presidente de la Cámara. Va a espiar la primera política del mazo!'
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
			bot.edit_message_text("No eres el canciller actual, no puedes elegir!", callback.from_user.id, callback.message.message_id)
			return
		if game.board.state.chairman is not None:
			# Ya se eligio en esta ronda: ignoro el click repetido.
			return

		chosen = game.playerlist[chosen_uid]
		game.board.state.chairman = chosen
		bot.edit_message_text("Elegiste a %s como Presidente de la Cámara!" % chosen.name,
			callback.from_user.id, callback.message.message_id)
		bot.send_message(game.cid,
			"El Canciller %s eligió a %s como Presidente de la Cámara." % (game.board.state.chancellor.name, chosen.name))
		game.history.append("El Canciller %s eligió a %s como Presidente de la Cámara." % (game.board.state.chancellor.name, chosen.name))

		# Mezclo antes de espiar para que la carta que ve sea la que realmente va a robar el presidente.
		shuffle_policy_pile(bot, game)
		top_policy = game.board.policies[0]
		bot.send_message(ADMIN if game.is_debugging else chosen.uid,
			"%s\nEspiaste la primera política del mazo: *%s*" % (game.groupName, top_policy), parse_mode=ParseMode.MARKDOWN)
		game.hiddenhistory.append("El Presidente de la Cámara %s espió %s" % (chosen.name, top_policy))
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
		btns.append([InlineKeyboardButton(policy, callback_data=strcid + "_" + policy)])
		hiddenhistory_text += policy.title() + " "
	hiddenhistory_text[:-1]
	# Guardo Historial secreto
	game.hiddenhistory.append(("*Ronda %d.%d*\nEl presidente %s recibió " % (game.board.state.liberal_track + game.board.state.fascist_track + 1, game.board.state.failed_votes + 1, game.board.state.president.name) ) + hiddenhistory_text)
	choosePolicyMarkup = InlineKeyboardMarkup(btns)
	if not game.is_debugging:
		bot.send_message(game.board.state.president.uid, f"{game.groupName}\nHas robado las siguientes 3 politicas. Cual quieres descartar?",
			reply_markup=choosePolicyMarkup)
	else:
		bot.send_message(ADMIN, f"{game.groupName} Has robado las siguientes 3 politicas. Cual quieres descartar?",
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
			msg = "No eres ni el presidente ni el canciller actual!"
			bot.edit_message_text(msg, uid,	callback.message.message_id)
			return

		# Si hay 3 politicas veo que sea el presidente el que descarte.
		if len(game.board.state.drawn_policies) == 3 and uid == game.board.state.president.uid:
			log.info("Player %s (%d) discarded %s" % (callback.from_user.first_name, uid, answer))
			politics = ','.join(game.board.state.drawn_policies)
			bot.edit_message_text("Robaste %s. La política %s va a ser descartada!" % (politics , answer), uid,
			callback.message.message_id)
			# remove policy from drawn cards and add to discard pile, pass the other two policies
			# Grabo en Hidden History que descarta el presidente.
			game.hiddenhistory.append("El presidente descartó " + answer)
			for i in range(3):
				if game.board.state.drawn_policies[i] == answer:
					game.board.discards.append(game.board.state.drawn_policies.pop(i))                                
					break
			pass_two_policies(bot, game)
		elif len(game.board.state.drawn_policies) == 2 and uid == game.board.state.chancellor.uid:
			# Si el canciller elije el boton de veto
			if answer == "veto" :
				log.info("Player %s (%d) suggested a veto" % (callback.from_user.first_name, uid))
				bot.edit_message_text("Has sugerido vetar al Presidente %s" % game.board.state.president.name, uid,
					callback.message.message_id)
				bot.send_message(game.cid,
					"El canciller %s sugirío Vetar al Presidente %s." % (
					game.board.state.chancellor.name, game.board.state.president.name))

				btns = [[InlineKeyboardButton("Veto! (aceptar sugerencia)", callback_data=strcid + "_yesveto")],
				[InlineKeyboardButton("No Veto! (rechazar sugerencia)", callback_data=strcid + "_noveto")]]

				vetoMarkup = InlineKeyboardMarkup(btns)
				bot.send_message(game.board.state.president.uid,
					"El canciller %s te sugirío Vetar. Quieres vetar (descartar) estas cartas?" % game.board.state.chancellor.name,
					reply_markup=vetoMarkup)
			else:
				# Si el canciller promulga...
				log.info("Player %s (%d) chose a %s policy" % (callback.from_user.first_name, uid, answer))
				bot.edit_message_text("La politica %s será promulgada!" % answer, uid,
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
		btns.append([InlineKeyboardButton(policy, callback_data=strcid + "_" + policy)])
	if game.board.state.fascist_track == 5 and not game.board.state.veto_refused:
		btns.append([InlineKeyboardButton("Veto", callback_data=strcid + "_veto")])
		choosePolicyMarkup = InlineKeyboardMarkup(btns)
		bot.send_message(game.cid,
			"El presidente %s entregó dos políticas al Canciller %s." % (
			game.board.state.president.name, game.board.state.chancellor.name))
		bot.send_message(game.board.state.chancellor.uid,
			"El Presidente %s te entregó las siguientes 2 políticas. Cuál quieres promulgar? También puedes usar el poder de Veto." % game.board.state.president.name,
		reply_markup=choosePolicyMarkup)
	elif game.board.state.veto_refused:
		choosePolicyMarkup = InlineKeyboardMarkup(btns)
		bot.send_message(game.board.state.chancellor.uid,
			"El presidente %s ha rechazado tu Veto. Ahora tienes que elegir. Cuál quieres promulgar?" % game.board.state.president.name,
			reply_markup=choosePolicyMarkup)
	elif game.board.state.fascist_track < 5:
		bot.send_message(game.cid,
			"El presidente %s entregó dos políticas al Canciller %s." % (
			game.board.state.president.name, game.board.state.chancellor.name))
		choosePolicyMarkup = InlineKeyboardMarkup(btns)
		if not game.is_debugging:
			bot.send_message(game.board.state.chancellor.uid,
				"El Presidente %s te entregó las siguientes 2 políticas. Cuál quieres promulgar?" % game.board.state.president.name,
				reply_markup=choosePolicyMarkup)
		else:
			bot.send_message(ADMIN,
				"El Presidente %s te entregó las siguientes 2 políticas. Cuál quieres promulgar?" % game.board.state.president.name,
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
		bot.send_message(game.cid, "El Presidente %s y el Canciller %s promulgaron una política %s!" % (game.board.state.president.name, game.board.state.chancellor.name, policy))
		game.history.append("El Presidente %s y el Canciller %s promulgaron una política %s!" % (game.board.state.president.name, game.board.state.chancellor.name, policy))
		if not hasattr(game, "formula_history"):
			game.formula_history = []
		game.formula_history.append({
			"round": game.board.state.currentround,
			"president_uid": game.board.state.president.uid,
			"chancellor_uid": game.board.state.chancellor.uid,
			"policy": policy,
		})
	else:
		bot.send_message(game.cid, "La política en la cima del mazo ha sido promulgada y es %s" % policy)
		game.history.append("La política en la cima del mazo ha sido promulgada y es %s" % policy)
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
					"Poder Presidencial habilitado: Investigar Políticas " + u"\U0001F52E" + "\nEl Presidente %s ahora conoce las proximas tres políticas "
					"en el mazo. El Presidente puede compartir "
					"(o mentir al respecto!) los resultados de su "
					"investigación a su propia discreción." % game.board.state.president.name)
				game.history.append("El presidente %s ahora conoce las proximas 3 políticas en el mazo." % game.board.state.president.name)
				action_policy(bot, game)                
			elif action == "kill":
				msg = "Poder Presidencial habilitado: Ejecución " + u"\U0001F5E1" + "\nEl Presidente %s tiene que matar a una persona. Pueden discutir la decisión ahora pero el Presidente tiene la última palabra." % game.board.state.president.name
				bot.send_message(game.cid, msg)
				game.board.state.fase = "legislating power kill"
				Commands.save_game(game.cid, "legislating power kill Round %d" % (game.board.state.currentround), game)
				action_kill(bot, game)				
			elif action == "inspect":
				bot.send_message(game.cid,
					"Poder Presidencial habilitado: Investigar Afiliación Política " + u"\U0001F50E" + "\nEl Presidente %s puede ver la afiliación política de un "
					"jugador. El Presidente puede compartir "
					"(o mentir al respecto!) los resultados de su "
					"investigación a su propia discreción." % game.board.state.president.name)
				game.board.state.fase = "legislating power inspect"
				Commands.save_game(game.cid, "legislating power inspect Round %d" % (game.board.state.currentround), game)				
				action_inspect(bot, game)
			elif action == "choose":
				bot.send_message(game.cid,
					"Poder Presidencial habilitado: Llamar a Elección Especial " + u"\U0001F454" + "\nEl Presidente %s puede elegir al próximo candidato presidencial. "
					"Despúes el orden continua "
					"normalmente." % game.board.state.president.name)
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
		bot.edit_message_text("Has aceptado el Veto!", uid, callback.message.message_id)
		bot.send_message(game.cid,
							"El Presidente %s ha aceptado el Veto del Canciller %s. No se ha promulgado una politíca pero esto cuenta como una elección fallida." % (
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
		bot.edit_message_text("Has rechazado el Veto!", uid, callback.message.message_id)
		bot.send_message(game.cid,
							"El Presidente %s ha rechazado el Veto del Canciller %s. El Canciller debe ahora elegir una política!" % (
								game.board.state.president.name, game.board.state.chancellor.name))
		pass_two_policies(bot, game)
	else:
		log.error("choose_veto: Callback data can either be \"veto\" or \"noveto\", but not %s" % answer)
    


def do_anarchy(bot, game):
	#log.info('do_anarchy called')	
	bot.send_message(game.cid, "ANARCHY!!")
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
        topPolicies += game.board.policies[i] + "\n"
    bot.send_message(game.board.state.president.uid,
                     "Las próximas 3 politicas son (La de arriba es la primera):\n%s\nPuedes mentir al respectosi quieres." % topPolicies)
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
		'Tienes que matar a una persona. Puedes discutir tu decisión con los otros. Elige sabiamente!',
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
        bot.edit_message_text("Has matado a %s!" % chosen.name, callback.from_user.id, callback.message.message_id)
        if chosen.role == "Hitler":
            bot.send_message(game.cid, "El Presidente " + game.board.state.president.name + " ha matado a " + chosen.name + ". ")
            game.board.state.game_endcode = 2
            end_game(bot, game, 2)
        else:
            bot.send_message(game.cid,
                             "El Presidente %s ha matado a %s que no era Hitler. %s, ahora estás muerto y no puedes hablar más!" % (
                                 game.board.state.president.name, chosen.name, chosen.name))
            bot.send_message(chosen.uid, "ESTAS MUERTO " + game.board.state.president.name + " TE HA MATADO")
            game.history.append("El Presidente %s ha matado a %s que no era Hitler!" % (game.board.state.president.name, chosen.name))
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
                     'Puedes elegir al próximo candidato a presidente. Después el orden vuelve a la normalidad. Elige sabiamente!',
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
        bot.edit_message_text("Has elegido a %s como el próximo presidente!" % chosen.name, callback.from_user.id,
                              callback.message.message_id)
        bot.send_message(game.cid,
                         "El Presidente %s ha elegido a %s como próximo presidente." % (
                             game.board.state.president.name, chosen.name))
        game.history.append("El Presidente %s ha elegido a %s como próximo presidente." % (game.board.state.president.name, chosen.name))
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
                     'Puedes ver la afiliación política de un jugador. A quien quieres elegir? Elige sabiamente!',
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
        bot.edit_message_text("La afiliación política de %s es %s" % (chosen.name, chosen.party),
                              callback.from_user.id,
                              callback.message.message_id)
        chosen.was_investigated = True
        bot.send_message(game.cid, "El Presidente %s ha inspeccionado a %s." % (game.board.state.president.name, chosen.name))
        game.history.append("El Presidente %s ha inspeccionado a %s." % (game.board.state.president.name, chosen.name))
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
			u"\U0001F576" + " Censura: de ahora en adelante el Canciller ya no elige Presidente de la Cámara.")
		game.history.append("Se activó la Censura: ya no se elige Presidente de la Cámara.")

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
		bot.send_message(game.cid, "El poder socialista no se puede usar y se saltea.")
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
			u"\U0001F41B" + " *Escucha Ilegal*: proponé a quién le van a ver la afiliación política.",
			lambda jugador: jugador.party != "socialista")
	elif power == "reclutamiento":
		_offer_socialist_power(bot, game, "reclutamiento", "socrec",
			u"\u270A" + " *Reclutamiento*: proponé a quién van a convertir en socialista.",
			lambda jugador: jugador.party != "socialista")
	elif power == "confesion":
		presidente = game.board.state.president
		_offer_socialist_power(bot, game, "confesion", "socconf",
			u"\U0001F4D6" + " *Confesión*: proponé quién va a ver la afiliación política del Presidente %s." % presidente.name,
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
	btns = [[InlineKeyboardButton("Sí, de acuerdo", callback_data=strcid + "_socvoto_si"),
		InlineKeyboardButton("No", callback_data=strcid + "_socvoto_no")]]
	markup = InlineKeyboardMarkup(btns)
	proponente = game.playerlist[proposer_uid].name
	for votante in votantes:
		bot.send_message(votante.uid,
			"%s\n%s propone *%s* para el poder socialista. ¿Estás de acuerdo?\nHace falta que estén de acuerdo *todos* los socialistas." % (
				game.groupName, proponente, chosen.name),
			reply_markup=markup, parse_mode=ParseMode.MARKDOWN)
	bot.send_message(proposer_uid,
		"Propusiste a *%s*. Esperando que el resto del partido esté de acuerdo..." % chosen.name,
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
			bot.edit_message_text("Esa decisión ya está resuelta.", uid, callback.message.message_id)
			return
		votantes = [p.uid for p in game.get_socialist_team(only_alive=True) if p.uid != propuesta["proposer"]]
		if uid not in votantes or uid in propuesta["approvals"]:
			return

		chosen = game.playerlist[propuesta["target"]]
		power = propuesta["power"]
		if voto == "no":
			# Sin unanimidad la propuesta se cae y se vuelve a abrir la eleccion para todos.
			log.info("Propuesta socialista de %s rechazada por %d" % (chosen.name, uid))
			bot.edit_message_text("Rechazaste la propuesta de %s." % chosen.name, uid, callback.message.message_id)
			game.board.state.socialist_proposal = None
			_avisar_socialistas(bot, game,
				"Un socialista *no estuvo de acuerdo* con %s. Vuelvan a elegir." % chosen.name,
				excepto_uid=uid)
			_ofrecer_poder_socialista(bot, game, power)
			return

		propuesta["approvals"].append(uid)
		bot.edit_message_text("Aceptaste la propuesta de %s." % chosen.name, uid, callback.message.message_id)
		if len(propuesta["approvals"]) < len(votantes):
			faltan = len(votantes) - len(propuesta["approvals"])
			bot.send_message(propuesta["proposer"],
				"Falta%s %d socialista%s por responder sobre %s." % ("n" if faltan > 1 else "", faltan, "s" if faltan > 1 else "", chosen.name))
			Commands.save_game(game.cid, "socialist proposal vote Round %d" % game.board.state.currentround, game)
			return

		# Unanimidad: se aplica el poder.
		game.board.state.socialist_proposal = None
		_avisar_socialistas(bot, game, "El partido se puso de acuerdo en *%s*." % chosen.name)
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
		"Poder Socialista habilitado: Escucha Ilegal " + u"\U0001F41B" + "\nLos socialistas van a ver la afiliación política de un jugador. Nadie más se entera de a quién eligieron.")
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
			bot.edit_message_text("Ya hay una propuesta en curso o el poder ya fue usado.", uid, callback.message.message_id)
			return
		chosen = game.playerlist[answer]
		bot.edit_message_text(u"\U0001F41B" + " Propusiste escuchar a %s." % chosen.name, uid, callback.message.message_id)
		_proponer_objetivo(bot, game, "escucha", uid, chosen)
	except Exception as e:
		log.error("choose_escucha: " + repr(e))
		log.exception(e)


def _aplicar_escucha(bot, game, chosen):
	log.info("Los socialistas escucharon a %s (%d): %s" % (chosen.name, chosen.uid, chosen.party))
	texto = u"\U0001F41B" + " Escucha Ilegal: la afiliación política de %s es *%s*" % (chosen.name, chosen.party)
	_avisar_socialistas(bot, game, texto)
	bot.send_message(game.cid, "Los socialistas ya usaron su Escucha Ilegal.")
	game.hiddenhistory.append("Los socialistas escucharon a %s (%s)" % (chosen.name, chosen.party))
	start_next_round(bot, game)


def action_reclutamiento(bot, game):
	log.info('action_reclutamiento called')
	bot.send_message(game.cid,
		"Poder Socialista habilitado: Reclutamiento " + u"\u270A" + "\nLos socialistas van a convertir a un jugador. Cuando terminen, revisá tu afiliación con /info: si te cambió, ahora ganás con los socialistas.")
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
			bot.edit_message_text("Ya hay una propuesta en curso o el poder ya fue usado.", uid, callback.message.message_id)
			return
		chosen = game.playerlist[answer]
		bot.edit_message_text(u"\u270A" + " Propusiste reclutar a %s." % chosen.name, uid, callback.message.message_id)
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
			u"\u270A" + " Los socialistas te reclutaron, pero sos *Hitler*: no te hace efecto. Seguí actuando como si nada, seguís ganando con los fascistas y no participás de sus decisiones. Eso sí, ahora tenés la carta socialista: quien te investigue va a ver *socialista*.",
			parse_mode=ParseMode.MARKDOWN)
		game.hiddenhistory.append("Los socialistas reclutaron a %s, que era Hitler: se queda con la carta socialista pero sigue siendo fascista." % chosen.name)
	else:
		log.info("Los socialistas reclutaron a %s (%d)" % (chosen.name, chosen.uid))
		bot.send_message(ADMIN if game.is_debugging else chosen.uid,
			u"\u270A" + " *Fuiste reclutado por los socialistas!* A partir de ahora tu afiliación es socialista y ganás con ellos. Tu rol y lo que sabías no cambian.",
			parse_mode=ParseMode.MARKDOWN)
		game.hiddenhistory.append("Los socialistas reclutaron a %s" % chosen.name)

	_avisar_socialistas(bot, game, u"\u270A" + " Reclutamiento: el partido eligió a *%s*." % chosen.name)
	bot.send_message(game.cid, "Los socialistas ya usaron su Reclutamiento. Revisen su afiliación con /info!")
	start_next_round(bot, game)


def action_plan_quinquenal(bot, game):
	log.info('action_plan_quinquenal called')
	# Si quedan menos de 3 politicas hay que mezclar ANTES de agregar las nuevas.
	shuffle_policy_pile(bot, game)
	game.board.policies += ["socialista", "socialista", "liberal"]
	game.board.policies = random.sample(game.board.policies, len(game.board.policies))
	msg = ("Poder Socialista habilitado: Plan Quinquenal " + u"\u0035\uFE0F\u20E3" +
		"\nSe agregaron 2 políticas socialistas y 1 liberal al mazo y se barajó. Ahora quedan %d políticas." % len(game.board.policies))
	bot.send_message(game.cid, msg)
	game.history.append(msg)
	game.hiddenhistory.append(msg)
	start_next_round(bot, game)


def action_congreso(bot, game):
	log.info('action_congreso called')
	bot.send_message(game.cid,
		"Poder Socialista habilitado: Congreso " + u"\U0001F3DB" + "\nLos socialistas se reconocen entre ellos.")
	originales = game.get_socialists()
	reclutados_uids = getattr(game.board.state, "recruited_uids", [])
	# Hitler no cuenta como socialista nuevo aunque tenga la carta: justamente por eso el
	# Congreso delata que el reclutado era el.
	nuevos = [game.playerlist[u] for u in reclutados_uids
		if u in game.playerlist and game.playerlist[u].party_efectiva() == "socialista"]

	nombres_originales = ", ".join(s.name for s in originales) or "nadie"
	for nuevo in nuevos:
		bot.send_message(ADMIN if game.is_debugging else nuevo.uid,
			u"\U0001F3DB" + " *Congreso*: los socialistas de origen son *%s*." % nombres_originales,
			parse_mode=ParseMode.MARKDOWN)

	if not reclutados_uids:
		aviso = u"\U0001F3DB" + " *Congreso*: todavía no reclutaron a nadie, así que no hay socialistas nuevos."
	elif not nuevos:
		# El unico reclutado no se convirtio: era Hitler.
		aviso = u"\U0001F3DB" + " *Congreso*: no hay ningún socialista nuevo, así que la persona que reclutaron era *Hitler*."
	else:
		aviso = u"\U0001F3DB" + " *Congreso*: el nuevo socialista es *%s*." % ", ".join(n.name for n in nuevos)
	for original in originales:
		if original.is_dead:
			continue
		bot.send_message(ADMIN if game.is_debugging else original.uid, aviso, parse_mode=ParseMode.MARKDOWN)
		if game.is_debugging:
			break
	game.hiddenhistory.append("Congreso: socialistas de origen %s / nuevos %s" % (
		nombres_originales, ", ".join(n.name for n in nuevos) or "ninguno"))
	start_next_round(bot, game)


def action_confesion(bot, game):
	log.info('action_confesion called')
	presidente = game.board.state.president
	if presidente is None:
		# Puede pasar si la politica salio por anarquia: no hay presidente que confiese.
		bot.send_message(game.cid, "Poder Socialista: Confesión " + u"\U0001F4D6" + "\nNo hay presidente en esta ronda, así que el poder se saltea.")
		start_next_round(bot, game)
		return
	bot.send_message(game.cid,
		"Poder Socialista habilitado: Confesión " + u"\U0001F4D6" + "\nEl Presidente %s le tiene que mostrar su afiliación política a quien elijan los socialistas." % presidente.name)
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
			bot.edit_message_text("Ya hay una propuesta en curso o el poder ya fue usado.", uid, callback.message.message_id)
			return
		chosen = game.playerlist[answer]
		bot.edit_message_text(u"\U0001F4D6" + " Propusiste que %s vea la afiliación del Presidente." % chosen.name,
			uid, callback.message.message_id)
		_proponer_objetivo(bot, game, "confesion", uid, chosen)
	except Exception as e:
		log.error("choose_confesion: " + repr(e))
		log.exception(e)


def _aplicar_confesion(bot, game, chosen):
	presidente = game.board.state.president
	log.info("Confesion: %s (%d) ve la afiliacion del presidente %s" % (chosen.name, chosen.uid, presidente.name))
	bot.send_message(ADMIN if game.is_debugging else chosen.uid,
		u"\U0001F4D6" + " *Confesión*: la afiliación política del Presidente %s es *%s*." % (presidente.name, presidente.party),
		parse_mode=ParseMode.MARKDOWN)
	# La confesion se hace a la vista de todos: el grupo si se entera de quien la recibio.
	bot.send_message(game.cid,
		"El Presidente %s le confesó su afiliación política a %s." % (presidente.name, chosen.name))
	game.history.append("El Presidente %s le confesó su afiliación política a %s." % (presidente.name, chosen.name))
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
				bot.send_message(uid, "¿Quieres ir a anarquia? (CUIDADO si la mitad de los jugadores elige SI no se espera)", reply_markup=voteMarkup)
		else:
			bot.send_message(ADMIN, game.board.print_board(game.player_sequence))
			bot.send_message(ADMIN, "¿Quieres ir a anarquia? (CUIDADO si la mitad de los jugadores elige SI no se espera)", reply_markup=voteMarkup)
			
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
		bot.edit_message_text("Gracias por tu voto: %s para la anarquia" % (answer), uid, callback.message.message_id)
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
		bot.send_message(uid, "Puedes cambiar tu voto aquí.\n¿Quieres ir a anarquia? (CUIDADO si la mitad de los jugadores elige SI no se espera)", reply_markup=voteMarkup)
		
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
			voting_text += nombre_jugador + " votó Ja!\n"
		elif game.board.state.votes_anarquia[player.uid] == "No":
			voting_text += nombre_jugador + " votó Nein!\n"
	if list(game.board.state.votes_anarquia.values()).count("Si") >= (len(game.player_sequence) / 2):  # because player_sequence doesnt include dead
		# VOTING WAS SUCCESSFUL
		log.info("Vamos a anarquia!")
		voting_text += "Debido a que la mayoria de los jugador ha decidido ir a anarquia se ejecuta la anarquia."		
		game.board.state.nominated_president = None
		game.board.state.nominated_chancellor = None
		bot.send_message(game.cid, voting_text, ParseMode.MARKDOWN)
		bot.send_message(game.cid, "\nNo se puede hablar ahora.")
		game.history.append(("Ronda %d.%d\n\n" % (game.board.state.liberal_track + game.board.state.fascist_track + 1, game.board.state.failed_votes + 1) ) + voting_text)
		# Avanzo la cantidad del lider asi el lider queda correctamente asignado
		# Se incrementa como mucho 2 ya que el ultimo incremento lo hace la anarquia
		for i in range(2 - game.board.state.failed_votes):
			increment_player_counter(game)		
		do_anarchy(bot, game)
	else:
		log.info("La gente no quiere anarquia")
		voting_text += "Al no quiso ir a anarquia"
		game.board.state.nominated_president = None
		game.board.state.nominated_chancellor = None
		bot.send_message(game.cid, voting_text, ParseMode.MARKDOWN)
		game.history.append(("Ronda %d.%d\n\n" % (game.board.state.liberal_track + game.board.state.fascist_track + 1, game.board.state.failed_votes + 1) ) + voting_text)
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
		bot.send_message(cid, 'No se ejecuto el comandoset_stats debido a: '+str(e))
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
	
	# Grabo detalles de la partida
	nuevos_logros = {}
	game.stats_game_id = None
	if game_endcode != 99:
		save_game_details(bot, game.print_roles(), game_endcode, game.board.state.liberal_track, game.board.state.fascist_track, game.board.num_players)
		nuevos_logros, game.stats_game_id = StatsExtended.save_extended_game_stats(game, game_endcode)


	#bot.send_message(cid, "Datos a guardar %s %s %s %s %s" % (game.print_roles(), str(game_endcode), str(game.board.state.liberal_track), str(game.board.state.fascist_track), str(game.board.num_players)))
		
	stats = get_stats(bot, cid)	
	if game_endcode == 99:
		if GamesController.games[cid].board is not None:
			bot.send_message(cid, "Juego cancelado!\n\n%s" % game.print_roles())
		else:
			bot.send_message(cid, "Juego cancelado!")
		set_stats("cancelgame", stats[5] + 1, bot, cid)
	else:
		if game_endcode == -2:
			bot.send_message(game.cid, "Juego finalizado! Los fascistas ganaron eligiendo a Hitler como Canciller!\n\n%s" % game.print_roles())
			set_stats("fascistwinhitler", stats[1] + 1, bot, cid)
		if game_endcode == -1:
			bot.send_message(game.cid, "Juego finalizado! Los fascistas ganaron promulgando 6 políticas fascistas!\n\n%s" % game.print_roles())
			set_stats("fascistwinpolicies", stats[2] + 1, bot, cid)
		if game_endcode == 1:
			bot.send_message(game.cid, "Juego finalizado! Los liberales ganaron promulgando 5 políticas liberales!\n\n%s" % game.print_roles())
			set_stats("liberalwinpolicies", stats[3] + 1, bot, cid)
		if game_endcode == 2:
			bot.send_message(game.cid, "Juego finalizado! Los liberales ganaron matando a Hitler!\n\n%s" % game.print_roles())
			set_stats("liberalwinkillhitler", stats[4] + 1, bot, cid)
		if game_endcode == 3:
			bot.send_message(game.cid, "Juego finalizado! Los socialistas ganaron promulgando toda su pista de políticas socialistas!\n\n%s" % game.print_roles())
			# La columna es nueva (la agrega DBCreate.sql), asi que puede no existir en bases viejas.
			if len(stats) > 6:
				set_stats("socialistwinpolicies", stats[6] + 1, bot, cid)
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
		bot.send_message(cid,
			"🏅 ¡Ahora podés usar /mvp para votar en privado quién fue el MVP de esta partida! "
			"Cuando todos los jugadores hayan votado se revela el resultado.")

	if game_endcode == 99:
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
		remaining_policies = "\nPoliticas restantes en el mazo:\n"		
		for i in range(len(game.board.policies)):
			remaining_policies += game.board.policies[i] + "\n"
		# Se comienza a obtener el historial oculto
		history_text = "Historial Oculto:\n\n" 
		for x in game.hiddenhistory:				
			history_text += x + "\n"
		bot.send_message(game.cid, history_text + remaining_policies, ParseMode.MARKDOWN)
	except Exception as e:
		bot.send_message(game.cid, str(e))
		log.error("Unknown error: " + str(e)) 
        
def inform_players(bot, game, cid, player_number):
	log.info('inform_players called')
	bot.send_message(cid,
		"Vamos a comenzar el juego con %d jugadores!\n%s\nVe a nuestro chat privado y mira tu rol secreto!" % (
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
				game.playerlist[uid].name, game.playerlist[uid].role, game.playerlist[uid].party))


def get_role_set(game, player_number):
    # El reparto de roles depende del modo: la expansion socialista tiene su propia tabla
    # (6 a 13 jugadores) y agrega el rol Socialista.
    if game.es_socialista():
        return list(socialistSets[player_number]["roles"])
    return list(playerSets[player_number]["roles"])


def print_player_info(game, player_number):
    if game.es_socialista():
        roles = socialistSets[player_number]["roles"]
        return ("Hay %d Liberales, %d Fascistas, Hitler y %d Socialistas. Hitler no conoce a nadie." % (
            roles.count("Liberal"), roles.count("Fascista"), roles.count("Socialista")))
    if player_number == 5:
        return "Hay 3 Liberales, 1 Fascista y Hitler. Hitler conoce quien es el Fascista."
    elif player_number == 6:
        return "Hay  4 Liberales, 1 Fascista y Hitler. Hitler conocer quienes quien es el Fascista."
    elif player_number == 7:
        return "Hay  4 Liberales, 2 Fascistas y Hitler. Hitler no conoce quienes son los Fascistas."
    elif player_number == 8:
        return "Hay  5 Liberales, 2 Fascistas y Hitler. Hitler no conoce quienes son los Fascistas."
    elif player_number == 9:
        return "Hay  5 Liberales, 3 Fascistas y Hitler. Hitler no conoce quienes son los Fascistas."
    elif player_number == 10:
        return "Hay  6 Liberales, 3 Fascistas y Hitler. Hitler no conoce quienes son los Fascistas."


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
		game.history.append("*No habia cartas suficientes en el mazo de políticas asi que he mezclado el resto con el mazo de descarte!*")
		game.hiddenhistory.append("*No habia cartas suficientes en el mazo de políticas asi que he mezclado el resto con el mazo de descarte!*")
		game.board.discards += game.board.policies
		game.board.policies = random.sample(game.board.discards, len(game.board.discards))
		game.board.discards = []		
		bot.send_message(game.cid,
			"No habia cartas suficientes en el mazo de políticas asi que he mezclado el resto con el mazo de descarte!")

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
	
def change_groupname(bot, update):
	cid = update.message.chat.id
	groupname = update.message.chat.title
	game = Commands.get_game(cid)
	game.groupName = groupname
	bot.send_message(ADMIN, text="El group en {cid} ha cambiado de nombre a {groupname}".format(groupname=groupname, cid=cid))

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
		bot.send_message(cid, "Este comando solo funciona en un grupo.")
		return
	miembros = GroupMembers.get_active_members(cid)
	if not miembros:
		bot.send_message(cid, "Todavia no tengo miembros registrados de este grupo. Se van registrando a medida que entran/salen del grupo o se unen a una partida con /join.")
		return
	menciones = ["[{}](tg://user?id={})".format(name, uid) for uid, name in miembros]
	texto = "📢 *Atención a todos!*\n" + "\n".join(menciones)
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

def main():
	GamesController.init() #Call only once
	db_status_text = init_db()

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
	dp.add_handler(CommandHandler("symbols", Commands.command_symbols))
	dp.add_handler(CommandHandler("stats", Commands.command_stats))
	dp.add_handler(CommandHandler("stats2", Commands.command_stats2))
	dp.add_handler(CommandHandler("logros", Commands.command_logros))
	dp.add_handler(CommandHandler("guess", Commands.command_guess))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*chooseGameGuess\*(.*)\*(-?[0-9]*)", callback=Commands.callback_guess_game))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)_guessf_(-?[0-9]*)", callback=Commands.callback_guess_fascist))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)_guessh_(-?[0-9]*)", callback=Commands.callback_guess_hitler))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)_guesspred_(-?[0-9]*)", callback=Commands.callback_guess_prediction))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)_guessskip_([a-z]+)", callback=Commands.callback_guess_skip))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)_guessconfirm", callback=Commands.callback_guess_confirm))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)_guessrestart", callback=Commands.callback_guess_restart))
	dp.add_handler(CommandHandler("mvp", Commands.command_mvp))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*chooseGameMvp\*(.*)\*(-?[0-9]*)", callback=Commands.callback_mvp_game))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)_mvpvote_(-?[0-9]*)", callback=Commands.callback_mvp_vote))
	dp.add_handler(CommandHandler("end", Commands.command_end))
	dp.add_handler(CommandHandler("guessresults", Commands.command_guessresults))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*chooseGameGuessResults\*(.*)\*(-?[0-9]*)", callback=Commands.callback_guessresults_game))
	dp.add_handler(CommandHandler("miguess", Commands.command_miguess))
	dp.add_handler(CallbackQueryHandler(pattern=r"(-?[0-9]*)\*chooseGameMiguess\*(.*)\*(-?[0-9]*)", callback=Commands.callback_miguess_game))
	dp.add_handler(CommandHandler("vincularstats", Commands.command_vincularstats))
	dp.add_handler(CommandHandler("vincularstats2", Commands.command_vincularstats2))
	dp.add_handler(CommandHandler("admin", Commands.command_admin))
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

	# Registrar el menú de comandos que Telegram muestra al escribir "/"
	try:
		updater.bot.set_my_commands([
			BotCommand("help", "Informacion de los comandos disponibles"),
			BotCommand("start", "Da un poco de informacion sobre Secret Hitler"),
			BotCommand("rules", "Link al sitio oficial con las reglas"),
			BotCommand("explainsocialista", "Explica el modo socialista y sus diferencias"),
			BotCommand("symbols", "Muestra los simbolos posibles en el tablero"),
			BotCommand("newgame", "Crea un nuevo juego o carga uno previo"),
			BotCommand("nextgame", "Guarda que queres jugar la proxima partida y te avisa cuando se cree"),
			BotCommand("join", "Te une a un juego existente"),
			BotCommand("startgame", "Comienza un juego cuando todos se unieron"),
			BotCommand("board", "Imprime el tablero actual"),
			BotCommand("history", "Imprime el historial del juego actual"),
			BotCommand("votes", "Imprime quien ha votado"),
			BotCommand("calltovote", "Avisa a los jugadores que hay que votar (o el MVP si ya termino)"),
			BotCommand("retirar", "Retira tu voto de Ja o Nein para volver a votar"),
			BotCommand("startautoja", "Activa tu voto automático Ja fuera de Zona Hitler"),
			BotCommand("stopautoja", "Desactiva tu voto automático Ja"),
			BotCommand("info", "Muestra tu informacion privada del juego"),
			BotCommand("jugadores", "Muestra los jugadores del juego"),
			BotCommand("leave", "Te saca de un juego existente"),
			BotCommand("stats", "Muestra las estadisticas"),
			BotCommand("stats2", "Muestra tus estadisticas nuevas vinculadas a tu ID"),
			BotCommand("logros", "Muestra tus logros desbloqueados"),
			BotCommand("guess", "Adivina en privado quienes son los fascistas y Hitler"),
			BotCommand("mvp", "Vota en privado al mejor jugador de la partida"),
			BotCommand("end", "Cierra la votacion de MVP sin esperar a que voten todos"),
			BotCommand("guessresults", "Reimprime los resultados de las adivinanzas"),
			BotCommand("miguess", "Muestra en privado tu propio resultado de /guess"),
			BotCommand("version", "Muestra la version actual del bot"),
			BotCommand("all", "Menciona a todos los miembros conocidos del grupo"),
		])
	except Exception as e:
		log.error(str(e))

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
