from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.ext import (CallbackContext)
import GamesController

from functools import wraps
import jsonpickle
import os
import psycopg2
from psycopg2 import sql
import urllib.parse
import logging as log

from BloodClocktower.Boardgamebox.Game import Game
from BloodClocktower.Boardgamebox.Player import Player
from BloodClocktower.Boardgamebox.Reminder import Reminder

from Constants.Config import ADMIN
from Utils import restricted, player_call
from typing import List
import re


log.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=log.INFO)
logger = log.getLogger(__name__)

urllib.parse.uses_netloc.append("postgres")
url = urllib.parse.urlparse(os.environ["DATABASE_URL"])

commands = [  # command description used in the "help" command
	'*Comandos de Inicio*',
    '/help - Te da informacion de los comandos disponibles',
    '/start - Da un poco de información sobre Blood on the Clocktower',
    '/rules - Te da un link al sitio oficial con las reglas de Blood on the Clocktower',
    '/newgame - Crea un nuevo juego o carga un juego previo',
    '/join - Te une a un juego existente',
    '/startgame - Comienza un juego existente cuando todos los jugadores se han unido',
    '/delete - Borra el juego actual',
    '/board - Imprime el tablero actual con la pista liberal y la pista fascista, orden presidencial y contador de elección',
    '/storyteller - Despues de comenzar la partida, el story teller debe ejecutar este comando para asignarse el role',
    '/leave - Salis de la partida si no ha comenzado todavia',
	'',   
    '*Comandos propios del Storyteller*',
    '/firstnight - Comandos que ejecuta la primera noche',
    '/night - Comando para pasar a la fase de noche, avanza el numero de días. Limpia acciones del dia.',
    '/day - Comando para pasar a la fase de dia,  ',
    '/kill - Mata al jugador actual /kill @nick',
    '/setplayerorder - Setea el orden de los jugadores /setplayerorder name1,name2,name3',
    '/clear - Limpia los votos de la nominacion actual',
    '/nominations - Abre las nominaciones',
    '/chopping - Manda al chopping block al nominado actual',
    '/execute - Executa al nominado en el chopping block',
    '/setrole - Setea el role de un jugador /setrole @jugador,ROL',
    '/readgamejson - Setea los datos del json generado por https://clocktower.online/ ',
    '/getreminders - Obtiene los recordatorios de los jugadores que tenga el ST',
	'/timer - Crea un timer de X cantidad de minutos, puede ser usado por cualquiera',
	'/grimoire - Muestra el grimorio en privado al ST',
	'',
    '*Comandos utiles para jugadores*',
	'/call - Avisa a los jugadores que se tiene que actuar',
    '/players - Muestra los jugadores y sus links',
    '/history - Imprime el historial del juego actual',
    '/claim - Comando para guardar en el historial general algo que uno reclama ser',
    '/whisper - Comando para comenzar un whisper con alguien /whisper @participant1, @participant2',
    '/endwhisper - Comando para terminar el whisper actual',    
    '/defense - Comando para dictar la defensa contra la nominacion actual',
    '/nominate - Comando para nominar a una persona uso: /nominate @nick,MOTIVO',
    '/tick - Pasa el reloj al siguiente jugador',
    '/vote - Vota al jugador nominado actualmente.',
    '/clearvote - Limpia el voto actual',
	'/notes [notas]- (Solo en privado) Escribe notas, o las visualiza',
    '',
	'Comandos Miscelaneos'
    '/refresh - Refresca la info de nombre y nick del jugador que lo ejecuta',
    '/info - Muestra informacion en privado al jugador actual sobre su rol y que hace',    
    '/id - Muestra el id de quien hace el comando',
    '/travel - Agrega al jugador actual a la partida',
]

def storyteller(func):
	@wraps(func)
	def wrapped(update, context, *args, **kwargs):
		user_id = update.effective_user.id
		cid = update.message.chat_id		
		game = get_game(cid)

		if user_id != game.storyteller:
			update.effective_message.reply_text("No tienes acceso, ya que no eres el Storyteller")
			return
		return func(update, context, *args, **kwargs)
	return wrapped

def player(func):
	@wraps(func)
	def wrapped(update, context, *args, **kwargs):
		uid = update.effective_user.id
		cid = update.message.chat_id		
		game = get_game(cid)

		# Si no es u jugador o el ST...
		if uid not in game.playerlist and uid != game.storyteller:
			update.effective_message.reply_text("No tienes acceso, ya que no eres jugador o storyteller")
			return
		return func(update, context, *args, **kwargs)
	return wrapped

def command_start(update: Update, context: CallbackContext):
	bot = context.bot

	cid = update.message.chat_id
	bot.send_message(cid,
"""Este es un bot para jugar Clock On The Bloodtower
A ver explicación completa la editamos y luego la pongo en el bot.

Blood on the clocktower es un juego de deducción social.
Hay dos equipos, el pueblo y el demonio.

El objetivo del pueblo es eliminar al demonio.

El objetivo del demonio es que queden 2 jugadores vivos, el siendo uno de ellos.

Los roles determinarán que poder tiene cada jugador y para que equipo juega.

La noche 0 algunos roles usan su poder y se pasa al día.

Desde ese momento se sigue de la siguiente forma:

DIA:
Los jugadores hablan entre ellos, se puede hablar en secreto (whisper) y se denomina gente para ser ejecutada.

Cada jugador *vivo* puede por día:
- *Acusar* una vez a un jugador.
- *Ser acusado* para ser ejecutado una vez.

Cuando un candidato es elegido el a usador normalmente explica los motivos de la acusación y el acusado explica porque es mala idea que lo ejecuten.

Luego comenzando con el jugador a la izquierda del acusado y en sentido de las agujas del reloj los jugadores votan SI o NO.

- Si la cantidad de SI iguala o supera a la mitad de jugadores VIVOS redondeando para arriba.

Entonces el jugador PUEDE  ser ejecutado (Se dice que va al chopping block), los jugadores pueden seguir acusando.

- Si otro jugador es acusado y supera en votos SI al jugador en el Chopping block el otro es liberado y ahora este es el que puede ser ejecutado.

- Si otro jugador es acusado e igual en votos SI al jugador en el chopping block, estos dos jugadores no son ejecutados.

Cualquiera de los dos casos de arriba no impide que se siga acusando gente.

Las acusaciones y votos siguen hasta que el Storyteller decida.

En ese momento si hay alguien que ejecutar se ejecuta y ese jugador muere.

Un jugador muerto pierde:
- El poder que tenía su personaje.
- Votar las veces que quiera en más acusaciones. A partir de ese momento solo puede votar UNA última vez en el juego.
- Acusar a un jugador.

Luego de la ejecución se hace de noche y los jugadores con poderes los usa.

Luego comienza un nuevo día.

----

Ahora algo a destacar es el rol del Storyteller cuyo objetivo es llegar al día X con 3 jugadores vivos y que la partida sea divertida.
Para lograr esto usa un arsenal de herramientas pero sin romper las reglas.

Por otro lado en el juego se puede hablar en secreto para esto utilizaremos una regla de juego que usan en discord en server semi oficial
Uno con sus vecinos puede hablar en secreto hasta 15 palabras. Para esto no debe avisar a nadie.
Luego tendrá hasta 3 charlas en secreto que tendrá que indicar con /whisper @usuario. El cual debe estar de acuerdo en hacerlo (ya que el gasta una de sus charlas al hacerlo).
Mientras habla en secreto no se puede hablar acá en el principal, hasta que termine el whisper
/endwhisper

Hablar en secreto en grupo, si se quiere se puede usar whisper adicionales para hablar con más de una persona. Pero gasta 1 whisper más por persona.
O sea que hablar con otras 2 personas constaría 2 whispers y con 3 usarías 3 whispers.

Por otro lado mientras se está en whisper con alguien se puede hablar con los vecinos.

También se puede usar un whisper para hablar más de 15 palabras con un vecino cada día.""", ParseMode.MARKDOWN)
	command_help(update, context)

def command_commands(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	cid = update.message.chat_id




def command_help(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	cid = update.message.chat_id
	help_text = "Los siguientes comandos están disponibles:\n"
	for i in commands:
		help_text += i + "\n"
	bot.send_message(cid, help_text, ParseMode.MARKDOWN)

def get_game(cid) -> Game:
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



def load_and_get_games() -> List[Game]:
	games = []

	conn = psycopg2.connect(
		database=url.path[1:],
		user=url.username,
		password=url.password,
		host=url.hostname,
		port=url.port
	)
	cursor = conn.cursor()
	query = "SELECT * FROM games_blood"

	cursor.execute(query)
	if cursor.rowcount > 0:
		# Si encuentro juegos los busco a todos y los cargo en memoria
		for table in cursor.fetchall():
			if table[0] not in GamesController.games.keys():
				get_game(table[0])
	conn.close()
	return list(GamesController.games.values())

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
	query = "SELECT * FROM games_blood WHERE id = %s;"
	cur.execute(query, [cid])
	dbdata = cur.fetchone()

	if cur.rowcount > 0:
		log.info("Gane found")
		jsdata = dbdata[3]
		log.info(jsdata)
		#log.info("jsdat = %s" % (jsdata))				
		game = jsonpickle.decode(jsdata)
		
		# For some reason the decoding fails when bringing the dict playerlist and it changes it id from int to string.
		# So I have to change it back the ID to int.				
		temp_player_list = {}		
		for uid in game.playerlist:
			temp_player_list[int(uid)] = game.playerlist[uid]
		game.playerlist = temp_player_list
		
		if game.board is not None and game.board.state is not None:
			temp_last_votes = {}
			for uid in game.board.state.last_votes:
				temp_last_votes[int(uid)] = game.board.state.last_votes[uid]
			game.board.state.last_votes = temp_last_votes

			temp_votes = {}
			for uid in game.board.state.votes:
				temp_votes[int(uid)] = game.board.state.votes[uid]
			game.board.state.votes = temp_votes
		#bot.send_message(cid, game.print_roles())
		conn.close()
		return game
	else:
		log.info("Game Not Found")
		conn.close()
		return None

@player
def command_board(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	game = get_game(cid)
	if game.board:
		board_text = game.board.print_board(game)
		board_message = bot.send_message(cid, board_text, ParseMode.MARKDOWN)
		game.board_message_id = board_message.message_id
		save_game(cid, "Game in join state", game)
	else:
		bot.send_message(cid, "No ha comenzado el juego todavia, para comenzar pone /startgame")

def command_rules(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id	
	msg = """Reglas de Blood on the clocktower
	"""
	bot.send_message(cid, msg, ParseMode.MARKDOWN)

def command_newgame(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	groupName = update.message.chat.title	

	game = get_game(cid)
	groupType = update.message.chat.type
	if groupType not in ['group', 'supergroup']:
		bot.send_message(cid, "Tienes que agregarme a un grupo primero y escribir /newgame allá!")
	elif game:
		bot.send_message(cid, "Hay un juego comenzado en este chat. Si quieres terminarlo escribe /cancelgame!")
	else:
		newGame = Game(cid, update.message.from_user.id, groupName)
		GamesController.games[cid] = newGame
		bot.send_message(cid, "Nuevo juego creado! Cada jugador debe unirse al juego con el comando /join.\nEl storyteller no debe unirse de esta forma, el sera asignado mas tarde\nEl iniciador del juego (o el administrador) pueden unirse tambien y escribir /startgame cuando todos se hayan unido al juego!")

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
		nick = update.message.from_user.username
		uid = update.message.from_user.id
	else:
		uid = update.message.from_user.id
		if uid == ADMIN[0]:
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
		bot.send_message(game.cid, f"Ya te has unido al juego, {fname}!")
	elif len(game.playerlist) >= 10:
		bot.send_message(game.cid, "Han llegado al maximo de jugadores. Por favor comiencen el juego con /startgame!")
	else:
		#uid = update.message.from_user.id		
		try:
			#Commented to dont disturb player during testing uncomment in production
			bot.send_message(uid, f"Te has unido a un juego en {groupName}. Pronto te dire cual es tu rol secreto.")
			# choose_posible_role(bot, cid, uid)

			game.add_player(uid, fname, nick)
			log.info("%s (%d) joined a game in %d" % (fname, uid, game.cid))
			if len(game.playerlist) > 4:
				bot.send_message(game.cid, fname + " se ha unido al juego. Escribe /startgame si este es el último jugador y quieren comenzar con %d jugadores!" % len(game.playerlist))
			elif len(game.playerlist) == 1:
				bot.send_message(game.cid, "%s se ha unido al juego. Hay %d jugador en el juego y se necesita 5-10 jugadores." % (fname, len(game.playerlist)))
			else:
				bot.send_message(game.cid, "%s se ha unido al juego. Hay %d jugadores en el juego y se necesita 5-10 jugadores" % (fname, len(game.playerlist)))
				# Luego dicto los jugadores que se han unido
			jugadoresActuales = "Los jugadores que se han unido al momento son:\n"
			for player in game.playerlist.values():
				jugadoresActuales += f"{player.name}\n"
			bot.send_message(game.cid, jugadoresActuales)
			save_game(cid, "Game in join state", game)
		except Exception:
			bot.send_message(game.cid, f"Jugador {fname} debes ir a @botontheclocktowerbot y darle /start")

def command_startgame(update: Update, context: CallbackContext):
	bot = context.bot	
	uid = update.message.from_user.id
	cid = update.message.chat_id
	
	game = get_game(cid)

	if not game:
		bot.send_message(cid, "No hay juego en este grupo crea un nuevo juego con /newgame")
	elif update.message.from_user.id not in ADMIN and update.message.from_user.id != game.initiator and bot.getChatMember(cid, update.message.from_user.id).status not in ("administrator", "creator"):
		bot.send_message(game.cid, "Solo el creador del juego o un admin puede iniciar con /startgame")	
	elif game.board:
		bot.send_message(cid, "El juego ya empezo!")		
	else:		
		# Verifico si la configuracion ha terminado y se han unido los jugadores necesarios		
		min_jugadores = 5		
		if len(game.playerlist) >= min_jugadores:
			save_game(cid, "Game in starting state", game)
			game.startgame()
			bot.send_message(game.cid, "El Storyteller debe poner aqui el comando /storyteller para ser reconocido como tal")
		else:
			bot.send_message(game.cid, "Falta el numero mínimo de jugadores. Faltan: %s " % (str(min_jugadores - len(game.playerlist))))

def command_storyteller(update: Update, context: CallbackContext):
	bot = context.bot	
	uid = update.message.from_user.id
	cid = update.message.chat_id	
	game = get_game(cid)

	fname = update.message.from_user.first_name.replace("_", " ")

	if game.storyteller is None:
		game.storyteller = uid
		bot.send_message(game.cid, f"El Storyteller es: {fname}, teman por sus vidas Aldeanos!!!")
		game.shuffle_player_sequence()
		bot.send_message(game.cid, f"Jugaremos Trouble Brewing, ya que es el unico modulo que tengo XD")
		bot.send_message(uid, "Eres el storyteller, prepara los roles y cuando quieras reparte los roles")
		bot.send_message(uid, "Con /firstnight en el grupo se hará la primera noche (No hace nada actualmente)")
		bot.send_message(uid, "Con /day comenzarás el primer día y luego con /night pasarás a la noche. Para ir al siguiente dia, pones /day nuevamente.")
	else:
		bot.send_message(game.cid, f"La partida ya tiene storyteller, vete de aquí maldito usurpador!!!")

def command_delete(update: Update, context: CallbackContext):
	bot = context.bot
	args = context.args
	log.info('command_cancelgame called {}'.format(args))
	cid = update.message.chat_id
	uid = update.effective_user.id
	#Always try to delete in DB	
	if len(args) > 0 and uid == ADMIN[0]:
		cid = int(args[0])	
	try:
		delete_game(cid)
		if cid in GamesController.games.keys():
			del GamesController.games[cid]
		bot.send_message(cid, "Borrado exitoso.")
	except Exception as e:
		bot.send_message(cid, "El borrado ha fallado debido a: "+str(e))

@storyteller
def command_firstnight(update: Update, context: CallbackContext):
	bot = context.bot	
	# uid = update.message.from_user.id
	cid = update.message.chat_id
	game = get_game(cid)
	bot.send_message(game.cid, f"Comienza la primera noche, todos... cierren los ojos...")

@storyteller
def command_day(update: Update, context: CallbackContext):
	bot = context.bot	
	cid = update.message.chat_id
	game = get_game(cid)
	game.set_day()
	bot.send_message(game.cid, "Todos, abran los ojos...")
	save_game(cid, "Day", game)
	if game.board.state.day is 1:
		bot.send_message(game.cid, """En el recondito pueblo de ravenswood bluff los aldeanos se despiertan por un grito ahogado en el centro del pueblo, al llegar encuentran a su querido storyteller empelado en una de las manecillas del reloj.

Esto es la obra de un demonio que mata durante la noche, pero durante el día toma la forma de uno de ustedes; su trabajo es encontrarlo y vengar a las almas de los caídos por el.
Mucha suerte""")

@storyteller
def command_night(update: Update, context: CallbackContext):
	bot = context.bot	
	cid = update.message.chat_id
	game = get_game(cid)
	game.set_night()	
	bot.send_message(game.cid, "Todos, cierren los ojos...")
	save_game(cid, "Night", game)

@storyteller
def command_kill(update: Update, context: CallbackContext):
	bot = context.bot	
	args = context.args
	cid = update.message.chat_id
	game = get_game(cid)
	uid = update.message.from_user.id

	# Si lo uso desde la pantalla del bot
	if game is None:
		games_with_me_as_storyteller = get_games_with_me_as_storyteller(uid)
		if len(games_with_me_as_storyteller) == 0:
			bot.send_message(cid, "*No estas dirigiendo ningun juego de Blood*", ParseMode.MARKDOWN)
			return
		elif len(games_with_me_as_storyteller) == 1:
			# Si solo esta en un solo juego hago la accion directa
			# Si es agregar entonces agrego la nota
			game = games_with_me_as_storyteller[0]
			player_name = ' '.join(args)		
			result_kill = game.kill_player(player_name)
			if result_kill[0]:
				save_game(cid, f"Matamos a {player_name}", game)
			# Me lo mando en privado porque la intencion fue hacerlo en privado		
			bot.send_message(uid, result_kill[1], ParseMode.MARKDOWN)
		else:
			# More than one game
			btnMarkup = create_choose_buttons(uid, ' '.join(args), "kill_player", games_with_me_as_storyteller, context)
			bot.send_message(uid, "En cual de estos grupos quieres hacer la acción?", reply_markup=btnMarkup)
			return
	else:
		# Busco el jugador a matar
		player_name = ' '.join(args)		
		result_kill = game.kill_player(player_name)
		if result_kill[0]:
			save_game(cid, f"Matamos a {player_name}", game)			
		bot.send_message(game.cid, result_kill[1], ParseMode.MARKDOWN)

def get_games_with_me_as_storyteller(uid):
	games = load_and_get_games()
	games_with_me_as_storyteller = [game for game in games if game.storyteller == uid and game.board != None]
	return games_with_me_as_storyteller

def create_choose_buttons(uid, data, action, game_list, context):
	btns = []
	for game in game_list:
		cid = game.cid
		# Creo el boton el cual eligirá el jugador
		txtBoton = game.groupName
		comando_callback = "choosegameblood"
		context.user_data[uid] = data
		context.user_data["accion"] = action
		datos = str(cid) + "*" + comando_callback + str(uid)
		btns.append([InlineKeyboardButton(txtBoton, callback_data=datos)])
	# Agrego boton de cancel
	txtBoton = "Cancel"
	datos = "-1*choosegameblood" + str(uid)
	btns.append([InlineKeyboardButton(txtBoton, callback_data=datos)])
	btnMarkup = InlineKeyboardMarkup(btns)
	return btnMarkup

@storyteller
def command_execute(update: Update, context: CallbackContext):
	bot = context.bot	
	args = context.args
	cid = update.message.chat_id
	game = get_game(cid)	
	result_execute = game.execute_player()
	if result_execute[0]:
		save_game(cid, f"Execute", game)			
	bot.send_message(game.cid, result_execute[1])	

def command_players(update: Update, context: CallbackContext):
	bot = context.bot	
	uid = update.message.from_user.id
	cid = update.message.chat_id	
	game = get_game(cid)	
	if not game:
		bot.send_message(game.cid, "No hay partida en este grupo")		
	jugadoresActuales = "Los jugadores que se han unido al momento son:\n"	
	for player in game.playerlist.values():
		jugadoresActuales += f"{player_call(player)}\n"			
	bot.send_message(game.cid, jugadoresActuales, ParseMode.MARKDOWN)

def command_leave(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	uid = update.effective_user.id

	game = get_game(cid)

	if not game:
		bot.send_message(cid, '‼‼*No hay juego del que salir*‼‼', ParseMode.MARKDOWN)
	else:
		if game.board:
			bot.send_message(cid, '‼‼*El juego ya empezo y el admin no permite salir de juegos ya empezados*‼‼', ParseMode.MARKDOWN)
		else:
			del game.playerlist[uid]
			bot.send_message(cid, '‼‼*Has salido exitosamente del juego*‼‼', ParseMode.MARKDOWN)

@player
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
			if uid in game.playerlist or uid is game.storyteller:								
				if len(args) > 0:
					#Data is being claimed
					claimtext = ' '.join(args)
					claimtexttohistory = f"El jugador {game.playerlist[uid].name} declara: {claimtext}"
					bot.send_message(cid, f"Tu declaración: {claimtext} fue agregada al historial.")
					game.history.append(claimtexttohistory)
					log.info(game.history)
					save_game(cid, "Claim", game)
				else:					
					bot.send_message(cid, "Debes mandar un mensaje para hacer una declaración.")

			else:
				bot.send_message(cid, "Debes ser un jugador del partido para declarar algo.")				
		else:
			bot.send_message(cid, "No hay juego en este chat. Crea un nuevo juego con /newgame")
	except Exception as e:
		bot.send_message(cid, str(e))
		log.error("Unknown error: " + str(e))  

def command_history(update: Update, context: CallbackContext):
	bot = context.bot
	#game.pedrote = 3
	#Send message of executing command   
	cid = update.message.chat_id
	#Check if there is a current game 
	
	groupName = update.message.chat.title

	game = get_game(cid)
	if game:			
		#bot.send_message(cid, "Current round: " + str(game.board.state.currentround + 1))
		uid = update.message.from_user.id
		game.groupName = groupName
		history_text_list = []
		history_text = f"Historial del grupo *{groupName}*:\n\n"			
		for x in game.history:
			if len(history_text) < 3500:
				history_text += f"{x}\n\n"
			else:
				history_text_list.append(history_text)
				history_text = f"{x}\n\n"
		history_text_list.append(history_text)
		for history_text_item in history_text_list:
			bot.send_message(uid, history_text_item, ParseMode.MARKDOWN)
		# if len(history_textContinue) > 0:
		# 	bot.send_message(uid, history_textContinue, ParseMode.MARKDOWN)
		#bot.send_message(cid, "I sent you the history to our private chat")			
	else:
		bot.send_message(cid, "No hay juego en este chat. Crea un nuevo juego con /newgame")	

@restricted
def command_debug(update: Update, context: CallbackContext):
	bot = context.bot	
	# uid = update.message.from_user.id
	cid = update.message.chat_id
	game = get_game(cid)
	game.is_debugging = True if not game.is_debugging else False
	bot.send_message(cid, "Debug Mode: ON" if game.is_debugging else "Debug Mode: OFF")

@player
def command_whisper(update: Update, context: CallbackContext):
	bot = context.bot	
	uid = update.message.from_user.id
	cid = update.message.chat_id
	game = get_game(cid)
	args = context.args	
	whispering_result = game.start_whisper(uid, ' '.join(args))
	if whispering_result[0]:
		save_game(cid, "Wshiper Created", game)
	bot.send_message(cid, whispering_result[1])

@player
def command_endwhisper(update: Update, context: CallbackContext):
	bot = context.bot	
	uid = update.message.from_user.id
	cid = update.message.chat_id
	game = get_game(cid)	
	whisper_message = game.end_whisper(uid)		
	save_game(cid, "Claim", game)
	bot.send_message(game.cid, whisper_message)	

@player
def command_nominate(update: Update, context: CallbackContext):
	bot = context.bot	
	args = context.args
	cid = update.message.chat_id
	uid = update.message.from_user.id
	game = get_game(cid)
	data = ' '.join(args).split(";")
	if len(data) == 2:
		# Busco el jugador a acusar
		player_name = data[0].strip()
		defender = game.find_player(player_name)
		accuser = game.playerlist[uid]
		if accuser.dead :
			bot.send_message(cid, "Un jugador muerto no puede nominar")
			return
		if defender is None:
			bot.send_message(cid, "El jugador ingresado no existe")
			return
		if not game.board.state.can_nominate:
			bot.send_message(cid, "El storyteller no ha habilitado las nominaciones")
			return

		accuser.nominated_someone = True
		defender.was_nominated = True

		game.board.state.accuser = accuser
		game.board.state.defender = defender
		game.board.state.accusation = data[1].strip()
		message_nomination = f"De repente {player_call(accuser)} se levanta y señala con el dedo a {player_call(defender)} deberias ir a la horca!\nMotivo: {game.board.state.accusation}"
		game.history.append(message_nomination)
		save_game(cid, f"Se nomino a: {defender.name}", game)		
		bot.send_message(game.cid, message_nomination, ParseMode.MARKDOWN)
		bot.send_message(game.cid, f"{player_call(defender)} debes hacer tu defensa con /defense Defensa", ParseMode.MARKDOWN)
	else:
		bot.send_message(game.cid, "Debes ingresar /nominate [Nombre jugador en Board];Texto Acusación")

@player
def command_defense(update: Update, context: CallbackContext):
	bot = context.bot	
	args = context.args
	cid = update.message.chat_id
	game = get_game(cid)
	state = game.board.state
	uid = update.message.from_user.id
	if len(args) > 0:
		# Si el jugador que defiende no es el defensor...
		# log.info(state.defender.uid)
		# log.info(uid)

		if state.defender.uid != uid:
			bot.send_message(game.cid, f"El mensaje debe ser enviado por {player_call(state.defender)}")
		defender = state.defender
		accuser = state.accuser		
		defensa = " ".join(args)

		bot.send_message(game.cid, f"Entonces {player_call(defender)} mira a los ojos a {player_call(accuser)} y dice a todo el pueblo: {defensa}", ParseMode.MARKDOWN)
		
		# Si es la primera que se hace defense se avanza el reloj
		if state.defense == None:
			clock_msg = game.advance_clock("")
			bot.send_message(cid, clock_msg, ParseMode.MARKDOWN)	
		state.defense = defensa

		board_text = game.board.print_board(game)
		board_message = bot.send_message(cid, board_text, ParseMode.MARKDOWN)
		game.board_message_id = board_message.message_id
		save_game(cid, "Defensa acusacion", game)
	else:
		bot.send_message(game.cid, "Debes ingresar algo para tu defensa")

@storyteller
def command_clear(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	game = get_game(cid)
	game.clear_nomination()
	bot.send_message(cid, "Se eliminó la acusación actual")
	save_game(cid, "Fix", game)

@storyteller
def command_toggle_nominations(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	game = get_game(cid)
	game.toggle_nominations()
	msg = "abierto" if game.board.state.can_nominate else "cerrado"
	bot.send_message(cid, f"Se han {msg} las nominaciones")
	save_game(cid, "Fix", game)
	
@storyteller
def command_set_player_order(update: Update, context: CallbackContext):
	bot = context.bot	
	args = context.args
	cid = update.message.chat_id
	game = get_game(cid)
	players = ' '.join(args)
	game.set_playerorder(players.split(","))
	save_game(cid, "Jugadores seteados", game)
	bot.send_message(game.cid, "Jugadores reorganizados")

@player
def command_tick(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	uid = update.message.from_user.id

	game = get_game(cid)
	result = game.tick(uid)
	if result[0]:
		save_game(cid, "Cloak Advance", game)
		update_board(bot, game, cid)
	bot.send_message(cid, result[1], ParseMode.MARKDOWN)

def update_board(bot, game, cid):
	board_text = game.board.print_board(game)
	# Si hay un board anterior lo borro
	if game.board_message_id:
		bot.deleteMessage(chat_id = cid, message_id = game.board_message_id)
		# bot.edit_message_text(board_text, cid, game.board_message_id, parse_mode=ParseMode.MARKDOWN)
	board_msg = bot.send_message(cid, board_text, ParseMode.MARKDOWN)
	game.board_message_id = board_msg.message_id

@player
def command_vote(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	uid = update.message.from_user.id
	game = get_game(cid)

	# if uid == game.storyteller and len(args) > 0:
	# Si el voto ya estaba no hago nada
	if uid in game.board.state.votes:
		return
	if game.can_modify_vote(uid):
		# Solo puede votar si esta vivo o si tiene el ultimo voto
		voter = game.playerlist[uid]
		if not voter.dead or (voter.dead and voter.has_last_vote):
			game.board.state.votes[uid] = "si"
			# Si el jugador esta muerto se le quita el ultimo voto
			if voter.dead:
				voter.has_last_vote = False
			save_game(cid, "Vote", game)
			board_text = game.board.print_board(game)
			update_board(bot, game, cid)
			if game.get_current_voter().uid == uid:
				bot.send_message(cid, "Has votado, puedes pasar al proximo jugador con /tick", ParseMode.MARKDOWN)
		else:
			bot.send_message(cid, "No puedes votar ya que estas muerto y has gastado tu voto haz /tick", ParseMode.MARKDOWN)
	else:
		bot.send_message(cid, "No puedes modificar tu voto porque ha pasado tu turno", ParseMode.MARKDOWN)


@player
def command_refresh(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	uid = update.message.from_user.id
	game = get_game(cid)
	player = game.playerlist[uid]
	player.name = update.message.from_user.first_name.replace("_", " ")
	player.nick = update.message.from_user.username
	save_game(cid, "Refresh Player Info", game)
	bot.send_message(cid, "Se ha modificado exitosamente al jugador", ParseMode.MARKDOWN)

@player
def command_info(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	uid = update.message.from_user.id
	game = get_game(cid)
	player = game.find_player_by_id(uid)
	
	if player is not None:
		role_data = game.get_role_info(player.role)
		bot.send_message(uid, f"""*Datos del jugador:*
Nombre: {player.name}
Nick: {player.nick}
Rol: {role_data["name"]}
Descripción del rol: {role_data["ability"]}
Afiliation : {player.afiliation}
Tipo de personaje: {role_data["team"]}""", ParseMode.MARKDOWN)

@player
def command_clearvote(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	uid = update.message.from_user.id
	game = get_game(cid)

	if uid not in game.board.state.votes:
		return

	if game.can_modify_vote(uid):
		game.board.state.votes.pop(uid, None)
		voter = game.playerlist[uid]
		# Si el votante estaba muerto y le quite el ultimo voto, se lo devuelvo.
		if voter.dead:
			voter.has_last_vote = True
		save_game(cid, "Clear Vote", game)
		board_text = game.board.print_board(game)
		update_board(bot, game, cid)
		if game.get_current_voter().uid == uid:
			bot.send_message(cid, "Has eliminado tu voto, puedes pasar al proximo jugador con /tick o votar con /vote", ParseMode.MARKDOWN)
	else:
		bot.send_message(cid, "*No puedes modificar tu voto porque ha pasado tu turno*", ParseMode.MARKDOWN)

@storyteller
def command_chopping(update: Update, context: CallbackContext):
	bot = context.bot	
	uid = update.message.from_user.id
	cid = update.message.chat_id
	game = get_game(cid)
	state = game.board.state

	if state.defender is not None:
		# Pone al defender en el chopping block
		state.chopping_block = state.defender
		state.chopping_block_votes = list(state.votes.values()).count("si")
		save_game(cid, "Chopping block", game)
		update_board(bot, game, cid)
	else:
		bot.send_message(cid, "No hay acusado para mandar al chopping block")
	# pone al defender actuan en el chopping block

def print_notes(game, uid, bot):
	history_text = "Notas partida en *{}*:\n\n".format(game.groupName)
	history_textContinue = "" 
	for x in game.playerlist[uid].notes:
		if len(history_text) < 3500:
			history_text += x + "\n\n"
		else:
			history_textContinue += x + "\n\n"

	bot.send_message(uid, history_text, ParseMode.MARKDOWN)
	if len(history_textContinue) > 0:
		bot.send_message(uid, history_textContinue, ParseMode.MARKDOWN)

def command_notes(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	uid = update.message.from_user.id
	args = context.args

	games = load_and_get_games()
	games_with_the_player = [game for game in games if uid in game.playerlist and game.board != None]

	if len(games_with_the_player) == 0:
		bot.send_message(cid, "*No estas en ningun juego de Blood*", ParseMode.MARKDOWN)
	elif len(games_with_the_player) == 1:
		# Si solo esta en un solo juego hago la accion directa
		# Si es agregar entonces agrego la nota
		first = games_with_the_player[0]
		if len(args) > 0:
			notes = ' '.join(args)
			first.add_note(uid, notes)
			save_game(first.cid, "Notes", first)
			bot.send_message(cid, f"{notes} fue agregada a la partida {first.groupName}", ParseMode.MARKDOWN)
		else:
			# Show notes
			print_notes(first, uid, bot)
	else:
		btns = []
		for game in games_with_the_player:
			notes = ' '.join(args)
			cid = game.cid
			# Creo el boton el cual eligirá el jugador
			txtBoton = game.groupName
			comando_callback = "choosegameblood"
			context.user_data[uid] = notes
			context.user_data["accion"] = "notas"
			datos = str(cid) + "*" + comando_callback + str(uid)
			btns.append([InlineKeyboardButton(txtBoton, callback_data=datos)])
		# Agrego boton de cancel
		txtBoton = "Cancel"
		datos = "-1*choosegameblood" + str(uid)
		btns.append([InlineKeyboardButton(txtBoton, callback_data=datos)])
		btnMarkup = InlineKeyboardMarkup(btns)
		bot.send_message(uid, "En cual de estos grupos quieres hacer la acción?", reply_markup=btnMarkup)



@player
def command_call(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	# uid = update.message.from_user.id
	game = get_game(cid)
	message = game.get_call_message()
	bot.send_message(game.cid, message, ParseMode.MARKDOWN)

@storyteller
def command_setrole(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	uid = update.message.from_user.id
	args = context.args

	games_with_me_as_storyteller = get_games_with_me_as_storyteller(uid)
	if len(games_with_me_as_storyteller) == 0:
		bot.send_message(cid, "*No estas dirigiendo ningun juego de Blood*", ParseMode.MARKDOWN)
	elif len(games_with_me_as_storyteller) == 1:
		# Si solo esta en un solo juego hago la accion directa
		# Si es agregar entonces agrego la nota
		first = games_with_me_as_storyteller[0]
		
		if len(args) > 0:
			data_string = ' '.join(args)
			data = data_string.split(";")
			if len(data) != 2:
				bot.send_message(cid, f"Te falta poner algun argumento es /setrole Usuario;Role", ParseMode.MARKDOWN)
				return
			elif len(data) == 2:
				message = game.set_role(data[0], data[1])
				save_game(first.cid, "setrole", first)
				bot.send_message(cid, message, ParseMode.MARKDOWN)			
		else:
			bot.send_message(cid, f"Tienes que poner /setrole Usuario;Role", ParseMode.MARKDOWN)
	else:
		btns = []
		for game in games_with_me_as_storyteller:
			notes = ' '.join(args)
			cid = game.cid
			# Creo el boton el cual eligirá el jugador
			txtBoton = game.groupName
			comando_callback = "choosegameblood"
			context.user_data[uid] = notes
			context.user_data["accion"] = "setrole"
			datos = str(cid) + "*" + comando_callback + str(uid)
			btns.append([InlineKeyboardButton(txtBoton, callback_data=datos)])
		# Agrego boton de cancel
		txtBoton = "Cancel"
		datos = "-1*choosegameblood" + str(uid)
		btns.append([InlineKeyboardButton(txtBoton, callback_data=datos)])
		btnMarkup = InlineKeyboardMarkup(btns)
		bot.send_message(uid, "En cual de estos grupos quieres hacer la acción?", reply_markup=btnMarkup)

def command_id(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	bot.send_message(cid, f"El id del usuario es {update.effective_user.id}", ParseMode.MARKDOWN)


def command_travel(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	uid = update.message.from_user.id
	fname = update.message.from_user.first_name.replace("_", " ")
	nick = update.message.from_user.username
	game = get_game(cid)
	if uid in game.playerlist:
		bot.send_message(cid, f"*{fname}* ya estas en el pueblo.", ParseMode.MARKDOWN)
		return
	game.add_player(uid, fname, nick)
	game.add_traveller(uid)
	save_game(cid, "Notes", game)
	bot.send_message(cid, f"Todos observan como *{fname}* llaga al pueblo", ParseMode.MARKDOWN)


def callback_timer(update: Update, context: CallbackContext):
	cid = update.message.chat_id
	bot = context.bot
	job_queue = context.job_queue
	args = context.args
	game = get_game(cid)
	# Si existe el juego verifico que tenga comando sino se usa el uso pensado del timer.
	if False:
		game.timer(update, context)
	else:
		# Default 1 minute y mensaje vacio
		try:
			minutos = int(args[0]) if len(args) > 0 else 1
			mensaje = " ".join(args[1:]) if len(args) > 1 else ""
		except Exception:
			minutos = 1
			mensaje = ""
		
		if minutos <= 1:
			msg = 'Se pone timer para {} segundos!'.format(minutos*60)
		elif minutos <= 60:
			msg = 'Se pone timer para {} minutos!'.format(minutos)
		else:
			msg = 'Se pone timer para {} horas!'.format(minutos/60)

		bot.send_message(chat_id=update.message.chat_id, text=msg)
		job_queue.run_once(callback_alarm, minutos*60, context=[update.message.chat_id, mensaje])

def callback_alarm(context: CallbackContext):
	job = context.job
	cid = job.context[0]
	mensaje = job.context[1]
	if mensaje == "":
		context.bot.send_message(cid, '‼‼*El tiempo ha terminado*‼‼', ParseMode.MARKDOWN)
	else:
		context.bot.send_message(cid, '‼‼*Acordate de {}*‼‼'.format(mensaje), ParseMode.MARKDOWN)

@storyteller
def command_getreminders(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	uid = update.message.from_user.id
	# args = context.args
	game = get_game(cid)
	reminders_text = ""
	for player in game.player_sequence:
		reminders_text += f"{game.get_player_reminders(player.name)}\n"
	bot.send_message(uid, reminders_text, ParseMode.MARKDOWN)

def command_readgamejson(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	uid = update.message.from_user.id
	args = " ".join(context.args)
	# Obtengo el json y lo convierto en objecto
	game_data = jsonpickle.decode(args)

	games_with_me_as_storyteller = get_games_with_me_as_storyteller(uid)
	if len(games_with_me_as_storyteller) == 0:
		bot.send_message(cid, "*No estas dirigiendo ningun juego de Blood*", ParseMode.MARKDOWN)
		return
	elif len(games_with_me_as_storyteller) == 1:
		game = games_with_me_as_storyteller[0]
		message = game.load_json_data(game_data)
		save_game(game.cid, "load_json_data", game)
		bot.send_message(cid, message, ParseMode.MARKDOWN)	
	else:
		btnMarkup = create_choose_buttons(uid, game_data, "load_json_data", games_with_me_as_storyteller, context)
		bot.send_message(uid, "En cual de estos grupos quieres hacer la acción?", reply_markup=btnMarkup)
		return

def command_grimoire(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	uid = update.message.from_user.id
	games_with_me_as_storyteller = get_games_with_me_as_storyteller(uid)
	if len(games_with_me_as_storyteller) == 0:
		bot.send_message(cid, "*No estas dirigiendo ningun juego de Blood*", ParseMode.MARKDOWN)
		return
	elif len(games_with_me_as_storyteller) == 1:
		game = games_with_me_as_storyteller[0]
		message = game.board.print_grimoire(game)
		bot.send_message(cid, message, ParseMode.MARKDOWN)	
	else:
		btnMarkup = create_choose_buttons(uid, "", "print_grimoire", games_with_me_as_storyteller, context)
		bot.send_message(uid, "En cual de estos grupos quieres hacer la acción?", reply_markup=btnMarkup)
		return

def callback_choose_game_blood(update: Update, context: CallbackContext):
	bot = context.bot
	callback = update.callback_query
	log.info('callback_choose_game_blood called: %s' % callback.data)	
	regex = re.search(r"(-[0-9]*)\*choosegameblood\*(.*)\*([0-9]*)", callback.data)
	cid, uid = int(regex.group(1)), int(regex.group(3)),
	
	if cid == -1:
		bot.edit_message_text("Cancelado", uid, callback.message.message_id)
		return
	
	game = get_game(cid)
	mensaje_edit = "Has elegido el grupo {0}".format(game.groupName)
	
	informacion = context.user_data[uid]
	accion = context.user_data["accion"]
	bot.edit_message_text(mensaje_edit, uid, callback.message.message_id)
	
	if accion == "notas":
		if len(informacion) > 0 :
			game.add_note(uid, informacion)
			save_game(cid, "Notes", game)
		else:
			print_notes(game, uid, bot)
	elif accion == "setrole":
		data = informacion.split(";")
		if len(data) != 2:
			bot.send_message(cid, f"Te falta poner algun argumento es /setrole Usuario;Role", ParseMode.MARKDOWN)
			return
		elif len(data) == 2:
			message = game.set_role(data[0], data[1])
			save_game(game.cid, "setrole", game)
			bot.send_message(cid, message, ParseMode.MARKDOWN)
	elif accion == "kill_player":
		player_name = informacion
		result_kill = game.kill_player(player_name)
		if result_kill[0]:
			save_game(cid, f"Matamos a {player_name}", game)			
		bot.send_message(uid, result_kill[1], ParseMode.MARKDOWN)
	elif accion == "load_json_data":
		context.user_data[uid]
		message = game.load_json_data(informacion)
		save_game(game.cid, "load_json_data", game)
		bot.send_message(cid, message, ParseMode.MARKDOWN)
	elif accion == "print_grimoire":
		message = game.board.print_grimoire(game)
		bot.send_message(cid, message, ParseMode.MARKDOWN)


@restricted
def command_fix(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	game = get_game(cid)
	state = game.board.state

	game.whisper_max = 3
	for player in game.player_sequence:
		player.whispering_count = 0
	
	bot.send_message(cid, "Fixed")
	save_game(cid, "Fix", game)

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
	query = "select * from games_blood where id = %s;"
	cur.execute(query, [cid])
	dbdata = cur.fetchone()
	if cur.rowcount > 0:
		log.info('Updating Game')
		gamejson = jsonpickle.encode(game)
		#query = "UPDATE games_blood SET groupName = %s, data = %s WHERE id = %s RETURNING data;"
		query = "UPDATE games_blood SET groupName = %s, data = %s WHERE id = %s;"
		cur.execute(query, (groupName, gamejson, cid))
		#log.info(cur.fetchone()[0])
		conn.commit()		
	else:
		log.info('Saving Game in DB')
		gamejson = jsonpickle.encode(game)
		query = "INSERT INTO games_blood(id , groupName, tipojuego , data) VALUES (%s, %s, %s, %s);"
		#query = "INSERT INTO games(id , groupName  , data) VALUES (%s, %s, %s) RETURNING data;"
		cur.execute(query, (cid, groupName, "blood", gamejson))
		#log.info(cur.fetchone()[0])
		conn.commit()
	conn.close()

def delete_game(cid):
	conn = psycopg2.connect(
		database=url.path[1:],
		user=url.username,
		password=url.password,
		host=url.hostname,
		port=url.port
	)
	cur = conn.cursor()
	#log.info("Deleting Game in DB")
	query = "DELETE FROM games_blood WHERE id = %s;"
	cur.execute(query, [cid])
	conn.commit()
	conn.close()
