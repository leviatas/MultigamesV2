import logging as log
import os
import traceback
import sys

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, \
	InlineQueryResultArticle, InputTextMessageContent
from telegram.constants import ParseMode
from telegram.ext import (Application, InlineQueryHandler, CommandHandler, \
	CallbackQueryHandler, MessageHandler, filters, CallbackContext)
from telegram.helpers import mention_html, escape_markdown

from Constants.Config import ADMIN
import BloodClocktower.Commands as Commands
import GamesController

import datetime
import pytz

from Utils import command_status

log.basicConfig(
    format='%(asctime)s - Blood - %(levelname)s - %(message)s',
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

def main(stop_event):
    log.info("Starting blood bot")
    GamesController.init() #Call only once

    token = os.environ.get('TOKEN_BLOOD', None)
    
    app = Application.builder().token(token).build()

    # on different commands - answer in Telegram
    app.add_handler(CommandHandler("start", Commands.command_start))
    app.add_handler(CommandHandler("help", Commands.command_help))
    app.add_handler(CommandHandler("board", Commands.command_board))
    app.add_handler(CommandHandler("rules", Commands.command_rules))
    app.add_handler(CommandHandler("debug", Commands.command_debug))

    app.add_handler(CommandHandler("newgame", Commands.command_newgame))
    app.add_handler(CommandHandler("join", Commands.command_join))
    app.add_handler(CommandHandler("startgame", Commands.command_startgame))
    app.add_handler(CommandHandler("storyteller", Commands.command_storyteller))
    app.add_handler(CommandHandler("delete", Commands.command_delete))
    app.add_handler(CommandHandler("leave", Commands.command_leave))
    
    # Comandos Storyteller
    app.add_handler(CommandHandler("firstnight", Commands.command_firstnight))
    app.add_handler(CommandHandler("night", Commands.command_night))
    app.add_handler(CommandHandler("day", Commands.command_day))
    app.add_handler(CommandHandler("kill", Commands.command_kill))
    app.add_handler(CommandHandler("setplayerorder", Commands.command_set_player_order))
    app.add_handler(CommandHandler("clear", Commands.command_clear))
    app.add_handler(CommandHandler("nominations", Commands.command_toggle_nominations))
    app.add_handler(CommandHandler("chopping", Commands.command_chopping))
    app.add_handler(CommandHandler("execute", Commands.command_execute))
    app.add_handler(CommandHandler("setrole", Commands.command_setrole))
    app.add_handler(CommandHandler("readgamejson", Commands.command_readgamejson))    
    app.add_handler(CommandHandler('getreminders', Commands.command_getreminders))
    app.add_handler(CommandHandler('getjsondata', Commands.command_getjsondata))

    #Comandos utiles para jugadores
    app.add_handler(CommandHandler('timer', Commands.callback_timer))    
    app.add_handler(CommandHandler("players", Commands.command_players))    
    app.add_handler(CommandHandler("history", Commands.command_history))
    app.add_handler(CommandHandler("claim", Commands.command_claim))
    app.add_handler(CommandHandler("whisper", Commands.command_whisper))
    app.add_handler(CommandHandler("endwhisper", Commands.command_endwhisper))
    app.add_handler(CommandHandler("defense", Commands.command_defense))
    app.add_handler(CommandHandler("nominate", Commands.command_nominate))    
    app.add_handler(CommandHandler("tick", Commands.command_tick))
    app.add_handler(CommandHandler("vote", Commands.command_vote))
    app.add_handler(CommandHandler("clearvote", Commands.command_clearvote))    
    
    app.add_handler(CommandHandler("refresh", Commands.command_refresh))
    app.add_handler(CommandHandler("info", Commands.command_info))
    app.add_handler(CommandHandler("notes", Commands.command_notes))
    app.add_handler(CommandHandler("call", Commands.command_call))

    app.add_handler(CommandHandler("id", Commands.command_id))
    app.add_handler(CommandHandler("travel", Commands.command_travel))
    app.add_handler(CommandHandler("grimoire", Commands.command_grimoire))
    app.add_handler(CommandHandler("glosary", Commands.command_glosary))

    # DEveloper commands
    app.add_handler(CommandHandler("fix", Commands.command_fix))
    app.add_handler(CommandHandler("bug", Commands.command_bug))
    app.add_handler(CommandHandler("feature", Commands.command_feature))
    app.add_handler(CommandHandler("reload", Commands.command_reload))
    app.add_handler(CommandHandler("issues", Commands.command_list_issues))    

    app.add_handler(CallbackQueryHandler(pattern=r"(-[0-9]*)\*choosegameblood\*(.*)\*([0-9]*)", callback=Commands.callback_choose_game_blood))

    app.add_handler(MessageHandler(filters.TEXT, command_status))

    job_que = app.job_queue

    
    # JobQueue.run_daily no longer accepts a `context` kwarg; schedule without extra data
    if job_que is not None:
        morning = datetime.time(13, 15, 0, 0, tzinfo=pytz.timezone("America/Argentina/Buenos_Aires"))
        job_que.run_daily(Commands.reload_last_workflow, morning)
    else:
        log.warning('JobQueue not available. Install with: pip install "python-telegram-bot[job-queue]"')
    
    # app.add_error_handler(error)

    app.post_init = notify_startup

	# Start the Bot
    # app.run_polling(timeout=30)
    while not stop_event.is_set():
        app.run_polling(timeout=5,stop_signals=None) 

async def notify_startup(application: Application):
    await application.bot.send_message(
        chat_id=ADMIN[0],
        text="✅ Nueva versión en línea"
    )