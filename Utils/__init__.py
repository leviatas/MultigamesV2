from functools import wraps
from Constants.Config import ADMIN
from PIL import Image
from io import BytesIO
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ChatAction, ParseMode, Update
from telegram.ext import CallbackContext
from random import randrange

import psycopg2
import urllib.parse
import os
import jsonpickle
import logging as log
import GamesController

log.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=log.INFO)
logger = log.getLogger(__name__)



urllib.parse.uses_netloc.append("postgres")
#url = urllib.parse.urlparse('postgres://osawfnidytbmgi:126714f9f3157ee10baa8046e48d287872788c8d1349ddba5dfd2a85de82d2a6@ec2-174-129-192-200.compute-1.amazonaws.com:5432/d79l0ugjdnfiac')
url = urllib.parse.urlparse(os.environ["DATABASE_URL"])

def restricted(func):
	@wraps(func)
	def wrapped(update, context, *args, **kwargs):
		user_id = update.effective_user.id
		if user_id != ADMIN[0]:
			update.effective_message.reply_text("No tienes acceso")
			return
		return func(update, context, *args, **kwargs)
	return wrapped

def send_typing_action(func):
    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        return func(update, context,  *args, **kwargs)

    return command_func

def choose_random(lista, exclude):
	# Filtro la lista y quito los que estan en exclude
	copy_list = [i for i in lista if i not in exclude]
	random_index = randrange(len(copy_list))
	random_player_id = copy_list[random_index]
	return copy_list[random_player_id]	
	

def showFirstLetter(frase):
	palabras = frase.split()
	resultado = []
	for palabra in palabras:
		char = palabra[0]
		resultado.append(char + "".join(r" \_ " for elem in palabra[1:]))
	return " ".join(resultado)

def basic_validation(game, uid):
	return game.board is not None and uid in game.playerlist

def starting_with(lst, start):
	for idx in range(len(lst)):
		yield  lst[(idx + start) % len(lst)]

# Remueve repetidos y devuelve ambas listas
def remove_same_elements_dict(last_votes):
	last_votes_to_lower = {key:val.lower() for key, val in last_votes.items()}	
	repeated_keys = []
	valores_last_votes_to_lower = list(last_votes_to_lower.values())#last_votes_to_lower.values()
	for key, value in last_votes_to_lower.items():
		if valores_last_votes_to_lower.count(value) > 1:
			repeated_keys.append(key)	
	return {key:val for key, val in last_votes.items() if key not in repeated_keys}, {key:val for key, val in last_votes.items() if key in repeated_keys}

def player_call(player):
	return "[{0}](tg://user?id={1})".format(player.name, player.uid)

def user_call(name, tg_id):
	return "[{0}](tg://user?id={1})".format(name, tg_id)

def next_player_after_active_player(game):
	if game.board.state.player_counter < len(game.player_sequence) - 1:
		return game.board.state.player_counter +1
	else:
		return 0

def next_player_certain_player(players, player):
	index_player = players.index(player)
	if index_player < len(players) - 1:
		return players[index_player+1]
	else:
		return players[0]
	
def previous_player_after_certain_player(players, player):
	index_player = players.index(player)
	return players[index_player-1]

def increment_player_counter(game):
	if game.board.state.player_counter < len(game.player_sequence) - 1:
		game.board.state.player_counter += 1
	else:
		game.board.state.player_counter = 0

def showImages(bot, cid, cartas, img_caption = ""):
	images = []
	for carta in cartas:
		images.append(get_img_carta(carta, "", 0, 0))

	widths, heights = zip(*(i.size for i in images))

	total_width = sum(widths)
	max_height = max(heights)

	new_im = Image.new('RGB', (total_width, max_height))

	x_offset = 0
	for im in images:
		new_im.paste(im, (x_offset,0))
		x_offset += im.size[0]

	bio = BytesIO()
	bio.name = 'image.jpeg'
	new_im.save(bio, 'JPEG')
	bio.seek(0)
	bot.send_photo(cid, photo=bio, caption=img_caption)

def get_img_carta(num_carta, url_imagen, fila, columna, image_width = 3, image_height = 3):
	# Por defecto es para iamgenes con cartas en 3X3
	cartas_aventura = []
	carta = cartas_aventura[num_carta]
	fila, columna = carta["fila"], carta["columna"]	
	url_img = url_imagen		
	img = Image.open(url_img)
	width, height = img.size
	widthCarta, heightCarta = width/image_width, height/image_height
	# Este switch se hace para corresponder al llamado del metodo, sino tendria que haber sido columna, fila.
	columna, fila = int(fila), int(columna)
	#log.info(img.size)
	x, y = (fila*widthCarta), (columna*heightCarta)
	#log.info(x)
	#log.info(y)
	left, top, right, bottom = x, y, widthCarta+x, heightCarta+y
	cropped = img.crop( ( left, top, right, bottom ) )
	return cropped

def get_config_data(game, config_name):
	# Si por algun motivo tira excepcion siempre se devuelve None
	try:

		return game.configs.get(config_name, None)				
	except Exception:
		return None

def simple_choose_buttons(bot, cid, uid, chat_donde_se_pregunta, comando_callback, mensaje_pregunta, opciones_botones, one_line = True, items_each_line = 3):
	
	#sleep(3)
	btns = []
	# Creo los botones para elegir al usuario
	if one_line:
		for key, value in opciones_botones.items():
			txtBoton = value
			datos = str(cid) + "*" + comando_callback + "*" + str(key) + "*" + str(uid)
			#log.info(datos)
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
		game = get_game(cid)
		if game is not None and game.is_debugging:
			chat_donde_se_pregunta = ADMIN[0]
		bot.send_message(chat_donde_se_pregunta, mensaje_pregunta, reply_markup=btnMarkup, parse_mode=ParseMode.MARKDOWN)
		GamesController.simple_choose_buttons_retry = False
	except Exception as e:
		# Si tira error y estoy debugeando intento mandar de nuevo pero si no intente anteriormente
		game = get_game(cid)
		if game is not None and game.is_debugging and not GamesController.simple_choose_buttons_retry:
			GamesController.simple_choose_buttons_retry = True
			simple_choose_buttons(bot, cid, ADMIN[0], ADMIN[0], comando_callback, mensaje_pregunta, opciones_botones, one_line, items_each_line)
		else:
			bot.send_message(ADMIN[0], 'Error en simple_choose_buttons {}'.format(e))

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

def load_game(cid):
	conn = psycopg2.connect(
		database=url.path[1:],
		user=url.username,
		password=url.password,
		host=url.hostname,
		port=url.port
	)
	cur = conn.cursor()			
	#log.info("Searching Game in DB")
	query = "SELECT * FROM games WHERE id = %s;"
	cur.execute(query, [cid])
	dbdata = cur.fetchone()

	if cur.rowcount > 0:
		#log.info("Game Found")
		jsdata = dbdata[3]
		
		#log.info(dbdata[0])
		#log.info(dbdata[1])
		#log.info(dbdata[2])
		#log.info(dbdata[3])
		#log.info("jsdata = %s" % (jsdata))				
		game = jsonpickle.decode(jsdata)
		
		# For some reason the decoding fails when bringing the dict playerlist and it changes it id from int to string.
		# So I have to change it back the ID to int.				
		temp_player_list = {}		
		for uid in game.playerlist:
			temp_player_list[int(uid)] = game.playerlist[uid]
		game.playerlist = temp_player_list
		
		if game.board is not None and game.board.state is not None and hasattr(game.board.state, 'last_votes'):
			temp_last_votes = {}
			for uid in game.board.state.last_votes:
				temp_last_votes[int(uid)] = game.board.state.last_votes[uid]
			game.board.state.last_votes = temp_last_votes
		
		if game.board is not None and game.board.state is not None and hasattr(game.board.state, 'enesperadeaccion'):
			temp_espera_accion = {}	
			for uid in game.board.state.enesperadeaccion:
				temp_espera_accion[int(uid)] = game.board.state.enesperadeaccion[uid]
			game.board.state.enesperadeaccion = temp_espera_accion
		return game
	else:
		#log.info("Game Not Found")
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
	#log.info("Deleting Game in DB")
	query = "DELETE FROM games WHERE id = %s;"
	cur.execute(query, [cid])
	conn.commit()
	conn.close()

def save_game(cid, groupName, game, gameType):
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
		query = "select * from games where id = %s;"
		cur.execute(query, [cid])
		if cur.rowcount > 0:
			#log.info('Updating Game')
			gamejson = jsonpickle.encode(game)
			#log.info(gamejson)
			#query = "UPDATE games SET groupName = %s, data = %s WHERE id = %s RETURNING data;"
			query = "UPDATE games SET groupName = %s, tipojuego = %s, data = %s WHERE id = %s;"
			cur.execute(query, (groupName, gameType, gamejson, cid))
			#log.info(cur.fetchone()[0])
			conn.commit()
			conn.close()	
		else:
			#log.info('Saving Game in DB')
			gamejson = jsonpickle.encode(game)
			#log.info(gamejson)
			query = "INSERT INTO games(id, groupName, tipojuego, data) VALUES (%s, %s, %s, %s) RETURNING data;"
			#query = "INSERT INTO games(id , groupName  , data) VALUES (%s, %s, %s) RETURNING data;"
			cur.execute(query, (cid, groupName, gameType, gamejson))
			#log.info(cur.fetchone()[0])
			conn.commit()
			conn.close()
	except Exception as e:
		log.info('No se grabo debido al siguiente error: '+str(e))
		conn.rollback()
	
def save(bot, cid, newGroupName = ''):
	try:		
		#groupName = "Prueba"
		game = GamesController.games.get(cid, None)
		gameType = game.tipo
		save_game(cid, game.groupName if newGroupName == '' else newGroupName , game, gameType )
		#bot.send_message(cid, 'Se grabo correctamente.')
		#log.info('Se grabo correctamente.')
	except Exception as e:
		bot.send_message(cid, 'Error al grabar '+str(e))

def get_base_data2(cid, uid):
	if uid in ADMIN:		
		game = get_game(cid)
		if not game:
			return None, None
		player = game.playerlist[uid]
		return game, player
	else:
		return None, None
		
def get_base_data(update: Update, context: CallbackContext):
	bot = context.bot	
	cid, uid = update.message.chat_id, update.message.from_user.id
	if uid in ADMIN:		
		game = get_game(cid)
		if not game:
			bot.send_message(cid, "No hay juego creado en este chat")
			return cid, uid, None, None
		player = game.playerlist[uid]
		return cid, uid, game, player
	else:
		return cid, uid, None, None

def simple_choose_buttons_only_buttons(bot, cid, uid, comando_callback, opciones_botones):
	#sleep(3)
	btns = []
	# Creo los botones para elegir al usuario
	for key, value in opciones_botones.items():
		txtBoton = value
		datos = str(cid) + "*" + comando_callback + "*" + str(key) + "*" + str(uid)
		#if comando_callback == "announce":
		#	bot.send_message(ADMIN[0], datos)
		btns.append([InlineKeyboardButton(txtBoton, callback_data=datos)])
	return InlineKeyboardMarkup(btns)

def command_status(update: Update, context: CallbackContext):
	bot = context.bot
	# cid = update.message.chat_id
	try:

		cid = update.channel_post.chat_id
		message = update.effective_message
		
		if cid == -1001768638126 and message.text == "status":
			bot.send_message(ADMIN[0], f'Status OK')
	except Exception as e:
		log.info('Fallo el hacer status')
		