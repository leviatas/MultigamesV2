import logging as log
import os
import traceback
import sys

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update, \
	InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import (InlineQueryHandler, Updater, CommandHandler, \
	CallbackQueryHandler, MessageHandler, Filters, CallbackContext)
from telegram.utils.helpers import mention_html, escape_markdown

from Constants.Config import ADMIN
import BloodClocktower.Commands as Commands
import GamesController

log.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=log.INFO)
logger = log.getLogger(__name__)

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

def main():
    log.info("Starting blood bot")
    GamesController.init() #Call only once

    token = os.environ.get('TOKEN_BLOOD', None)
    updater = Updater(token, use_context=True)
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", Commands.command_start))
    dp.add_handler(CommandHandler("help", Commands.command_help))
    dp.add_handler(CommandHandler("board", Commands.command_board))
    dp.add_handler(CommandHandler("rules", Commands.command_rules))

    dp.add_handler(CommandHandler("newgame", Commands.command_newgame))
    dp.add_handler(CommandHandler("join", Commands.command_join))
    dp.add_handler(CommandHandler("startgame", Commands.command_startgame))
    dp.add_handler(CommandHandler("storyteller", Commands.command_storyteller))
    dp.add_handler(CommandHandler("delete", Commands.command_delete))
    # Comandos para avanzar el dia y el juego
    dp.add_handler(CommandHandler("firstnight", Commands.command_firstnight))
    dp.add_handler(CommandHandler("night", Commands.command_night))
    dp.add_handler(CommandHandler("day", Commands.command_day))
    # Comandos sobre los jugadores
    dp.add_handler(CommandHandler("kill", Commands.command_kill))

    #Comandos utiles para jugadores
    dp.add_handler(CommandHandler("players", Commands.command_players))
    dp.add_handler(CommandHandler("leave", Commands.command_leave))
    dp.add_handler(CommandHandler("history", Commands.command_showhistory))
    dp.add_handler(CommandHandler("claim", Commands.command_claim))	
    
    
    dp.add_error_handler(error)

    updater.bot.send_message(ADMIN[0], "Nueva version en linea")

    updater.start_polling(timeout=30)
    updater.idle()
