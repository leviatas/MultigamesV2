
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update, \
	InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import (InlineQueryHandler, Updater, CommandHandler, \
	CallbackQueryHandler, MessageHandler, Filters, CallbackContext)
from telegram.utils.helpers import mention_html, escape_markdown

import os
import configparser
import re
import datetime
import logging as log

from reportBot.reportModule import save_report, get_reports
from reportBot.userModule import save_user, get_users, get_users_with_missing_last_report
from reportBot.Models.ReporteModel import ReporteModel
from reportBot.Models.UserModel import UserModel

log.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=log.INFO)
logger = log.getLogger(__name__)

REPORT_BOT_TOKEN = os.environ.get('TOKEN_SPACE_HELPER', None)

if REPORT_BOT_TOKEN is None:
	config = configparser.ConfigParser()
	config.read('init.ini')
	REPORT_BOT_TOKEN = config['ENVIROMENT']['TOKEN_SPACE_HELPER']

def command_start(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	bot.send_message(cid, "Space Explorer Companion bot.")

def command_reports(update: Update, context: CallbackContext):
    bot = context.bot
    cid = update.message.chat_id
    args = " ".join(context.args)
    reports = get_reports("", args)
    txt = f"{reports[0]}\n"
    for reporte in reports[1]:
        txt += f"{reporte.get_formated_report()}\n"
    bot.send_message(cid, txt)

def command_getme(update: Update, context: CallbackContext):
    uid = update.effective_user.id
    cid = update.message.chat_id
    bot = context.bot
    result = get_users(uid)  
    if result[1] is None:
        mensaje = result[0]
    else:
        mensaje = result[1][0].get_call()
    bot.send_message(cid, mensaje, ParseMode.MARKDOWN)

def command_getusers(update: Update, context: CallbackContext):
    uid = update.effective_user.id
    cid = update.message.chat_id
    bot = context.bot
    results = get_users()
    usuarios = sorted(get_users()[1], key=lambda x: x.guild, reverse=True)
    txt = ""
    for reporte in usuarios:
        txt += f"{reporte.get_call()}\n"
    
    bot.send_message(cid, txt, ParseMode.MARKDOWN)



def command_last(update: Update, context: CallbackContext):
    uid = update.effective_user.id
    cid = update.message.chat_id
    bot = context.bot
    now = datetime.datetime.now()
    fecha_batalla = 23 if (now.time() < datetime.time(7,0,0) or now.time() > datetime.time(23,0,0)) else \
                    (7 if now.time() < datetime.time(15,0,0) else 15)

    report_date = now.replace(day=now.day, hour=fecha_batalla, minute=0,\
                                        second=0, microsecond=0)
    report_date = report_date - (datetime.timedelta(days=1) if now.time() < datetime.time(7,0,0) else datetime.timedelta(minutes=0))

    
    users_with_missing_reports = get_users_with_missing_last_report(report_date)

    txt = f"{users_with_missing_reports[0]}\n"
    for usuario in users_with_missing_reports[1]:
        txt += f"{usuario.get_call()}\n"
    bot.send_message(cid, txt, ParseMode.MARKDOWN)

def report_added(update: Update, context: CallbackContext):
    bot = context.bot
    cid = update.message.chat_id
    forward_from_name = update.message.forward_from.username
    forward_from_id = update.message.forward_from.id
    forward_date = update.message.forward_date
    uid = update.effective_user.id

    # (?<!\n) Me aseguro que no hay lineas anteriores asi evito montruos y ambush
    # Luego tomo lo necesario.
    m = re.search('(?<!\n)(.+)(\[.+\])(.+) ⚔:(\d+).+🛡:(\d+).+Lvl: (\d+)\n.+\n🔥Exp: (\d+)\n💰Gold: (-?\d+)(?:\n📦Stock: (-?\d+)\n)?(?:❤️Hp: -?(\d+))?', update.message.text)
    
    if m == None:
        bot.send_message(uid, "El reporte no es válido, posiblemente es un reporte de monstruo.")

    fecha_batalla = 23 if (forward_date.time() < datetime.time(7,0,0) or forward_date.time() > datetime.time(23,0,0)) else \
                    (7 if forward_date.time() < datetime.time(15,0,0) else 15)

    report_date = forward_date.replace(day=forward_date.day, hour=fecha_batalla, minute=0,\
                                        second=0, microsecond=0)
    report_date = report_date - (datetime.timedelta(days=1) if (forward_date.time() < datetime.time(7,0,0) ) else datetime.timedelta(minutes=0))
	
    #(self, report_date, chat_wars_name, castle, guild, attack, \
    # defense, player_level, experience, gold, stock, lost_hp)    
    castle = m.group(1)
    chat_wars_name = m.group(3)
    guild = m.group(2)
    attack = m.group(4)
    defense = m.group(5)
    player_level = m.group(6)
    experience = m.group(7)
    gold = m.group(8)
    stock = m.group(9) if m.group(9) is not None else "0"
    lost_hp = m.group(10) if m.group(10) is not None else "0"

    report = ReporteModel(report_date, chat_wars_name, castle, guild, attack, \
                defense, player_level, experience, gold, stock, lost_hp)
    result = save_report(report)

    bot.send_message(uid, result)

    bot.send_message(uid, 
f"Reporte enviado del bot *{forward_from_name} Id: ({forward_from_id})*\n\
Reporte de la batalla de las *{report_date}*\n\
El usuario es del castillo {castle}\n\
El usuario es del guild {guild}\n\
El usuario se llama en CW {chat_wars_name}\n\
El usuario tiene un ataque de {attack}\n\
El usuario tiene una defensa de {defense}\n\
El usuario es de nivel {player_level}\n\
El usuario gano {experience} de experiencia\n\
El usuario gano {gold} de oro\n\
El usuario gano {stock} stock\n\
El usuario perdio {lost_hp} de hp\n\
el mensaje fue creado *{forward_date}\n*\
El mensaje original es\n\
{update.message.text}", ParseMode.MARKDOWN)
    # Obtengo el id del usuario que esta enviando el reporte
    # y lo asocio a la cuenta de CW que lo envia si todavia no esta agregado    
    result = save_user(UserModel(uid, chat_wars_name))
    #bot.send_message(uid, result)

def reply_time(update: Update, context: CallbackContext):
    bot = context.bot
    cid = update.message.chat_id

    log.info(update.message)

    forward_from_name = update.message.reply_to_message.forward_from.username
    
    forward_date = update.message.reply_to_message.forward_date
    uid = update.effective_user.id

    chat_data = context.chat_data

    bot.send_message(cid, f"Forward from {forward_from_name} {forward_date}", ParseMode.MARKDOWN)

def begin_count(update: Update, context: CallbackContext):
    bot = context.bot
    cid = update.message.chat_id

    log.info(update.message)

    forward_from_name = update.message.reply_to_message.forward_from.username
    forward_from_id = update.message.reply_to_message.chat_id
    forward_date = update.message.reply_to_message.forward_date
    #uid = update.effective_user.id

    chat_data = context.chat_data

    chat_data["begin"] = forward_date

    bot.send_message(cid, f"Forward from {forward_from_name} {forward_date}", ParseMode.MARKDOWN)

def time_passed(update: Update, context: CallbackContext):
    bot = context.bot
    cid = update.message.chat_id

    chat_data = context.chat_data

    if chat_data["begin"]:
        now = update.message.date
        #nowapp = datetime.datetime.now(datetime.timezone.utc)
        diff = now - chat_data["begin"]
        bot.send_message(cid, f"Time passed {diff}", ParseMode.MARKDOWN)
    else:
        bot.send_message(cid, f"You have to do /begin_time in a forwarded message", ParseMode.MARKDOWN)
    

def main():
    updater = Updater(REPORT_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", command_start))
    dp.add_handler(CommandHandler("reports", command_reports))
    dp.add_handler(CommandHandler("me", command_getme))
    dp.add_handler(CommandHandler("users", command_getusers))
    dp.add_handler(CommandHandler("last", command_last))
    # dp.add_handler(MessageHandler(Filters.regex("Your result on the battlefield"), report_added))
    dp.add_handler(CommandHandler("time", reply_time))
    dp.add_handler(CommandHandler("begin_count", begin_count))
    dp.add_handler(CommandHandler("time_passed", time_passed))
    updater.start_polling(timeout=30)
    updater.idle()

if __name__ == '__main__':
    main()
