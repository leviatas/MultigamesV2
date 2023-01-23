
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

# from reportBot.reportModule import save_report, get_reports
# from reportBot.userModule import save_user, get_users, get_users_with_missing_last_report
# from reportBot.Models.ReporteModel import ReporteModel
# from reportBot.Models.UserModel import UserModel

log.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=log.INFO)
logger = log.getLogger(__name__)

REPORT_BOT_TOKEN = os.environ.get('TOKEN_GUILD', None)

if REPORT_BOT_TOKEN is None:
	config = configparser.ConfigParser()
	config.read('init.ini')
	REPORT_BOT_TOKEN = config['ENVIROMENT']['TOKEN_GUILD']

def command_start(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	bot.send_message(cid, "Bot mediocre para guild IVI")

def command_help(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	bot.send_message(cid, """
Comandos disponibles:
/start Comienza algo
/melody Datos para el puesto de melody
/lancelot Datos para el puesto de lancelot
/crappy_channels Canales que no valen la pena seguir
/paralian Saludo a paralian que pronto nos hara una imagen
/nixth_regala_pogs Para pedirle pogs a nixth
""")

def command_melody(update: Update, context: CallbackContext):
    bot = context.bot
    cid = update.message.chat_id
    SendButtonURL(bot, cid, "Melody", "https://t.me/share/url?url=/ws_l2Thy", "@Ale_Guetta")

def SendButtonURL(bot, cid, name, url, ownderCall):
    btn = [[InlineKeyboardButton(f"{name}'s", url=url)]]
    rulesMarkup = InlineKeyboardMarkup(btn)
    bot.send_message(cid, f"Link to {name}'s crappy shop. {ownderCall} OPEN UP", reply_markup=rulesMarkup)

def command_channels(update: Update, context: CallbackContext):
    bot = context.bot
    cid = update.message.chat_id
    
    channels = [("https://t.me/useless_sentinel", "Useless Sentinel"), ("https://t.me/RangerTales", "Ranger Tales"), \
                ("https://t.me/alwayssmile4me", "Always smile 4 me"), ("https://t.me/Diario_de_un_tiburon", "Diario de un tiburón"), \
                ("https://t.me/narakaslife", "Narakas Life"), ("https://t.me/CursedCamelotForge", "Cursed Camelot Forge"),\
                ("https://t.me/divineshadowsBRUH", "Divine Shadows Legacy")]
    btn = []
    for channel in channels:
        btn.append([InlineKeyboardButton(channel[1], url=channel[0])])

    rulesMarkup = InlineKeyboardMarkup(btn)
    bot.send_message(cid, f"Link to crappy IVI channels.", reply_markup=rulesMarkup)

def command_lancelot(update: Update, context: CallbackContext):
    bot = context.bot
    cid = update.message.chat_id
    SendButtonURL(bot, cid, "Lancelot", "https://t.me/share/url?url=/ws_6hphV", "@SirLancelotDuLac")

def command_paralian(update: Update, context: CallbackContext):
    bot = context.bot
    cid = update.message.chat_id
    bot.send_message(cid, f"**Bienvenida Paralian!!!**", parse_mode=ParseMode.MARKDOWN)

def command_nixth_regala_pogs(update: Update, context: CallbackContext):
    bot = context.bot
    cid = update.message.chat_id
    bot.send_message(cid, f"**¿Cómo? ¿Vos no recibiste el bono de navidad? A mi me dio 200 pogs...**", parse_mode=ParseMode.MARKDOWN)


def pot_request(update: Update, context: CallbackContext):
    bot = context.bot
    cid = update.message.chat_id    
    uid = update.effective_user.id
    # (?<!\n) Me aseguro que no hay lineas anteriores asi evito montruos y ambush
    # Luego tomo lo necesario.
    m = re.search('Pot (rage|peace|morph) (\d+)', update.message.text)
    
    if m == None:
        bot.send_message(cid, "No entendi tu pedido de potas, posiblemente sos malo escribiendo.")

    bot.send_message(cid, f"Entonces necesitas pot de {m.group(1)} y en cantidad {m.group(2)}, estoy procesando. Leviatas es un genio. *Les recuerdo que el no me esta haciendo decir esto...*", parse_mode=ParseMode.MARKDOWN)

    if(m.group(1) == "rage"):
        cantidad = int(m.group(2))           
        storm = 2 * cantidad
        white = 1 * cantidad
        sanguine = 1 * cantidad
        caveGarlic = 1 * cantidad
        cliffRue = 1 * cantidad
        sunTarragon = 1 * cantidad
        bot.send_message(cid, f"""Not enough materials to craft crappy rage pots. @nixth @Cocytus0 @nick_the_dick
Required:
 {white} x White Blossom
 {sanguine} x Sanguine Parsley
 {storm} x Storm Hyssop
 {sunTarragon} x Sun Tarragon
 {cliffRue} x Cliff Rue
 {caveGarlic} x Cave Garlic""")

    if(m.group(1) == "peace"):
        cantidad = int(m.group(2))
        caveGarlic = 2 * cantidad        
        ashRosemary = 1 * cantidad
        swampLavander = 1 * cantidad
        stinkSumac = 1 * cantidad
        storm = 1 * cantidad
        grass = 1 * cantidad
        
        bot.send_message(cid, f"""Not enough materials to craft crapp peace pots. @nixth @Cocytus0 @nick_the_dick
Required:
 {storm} x Storm Hyssop
 {ashRosemary} x Ash Rosemary
 {swampLavander} x Swamp Lavender
 {stinkSumac} x Stinky Sumac
 {grass} x Tecceagrass
 {caveGarlic} x Cave Garlic""")
    if(m.group(1) == "morph"):
        cantidad = int(m.group(2))
        maccunut = 3 * cantidad

        silverOre = 10 * cantidad
        powder = 4 * cantidad
        grass = 2 * cantidad
        #silverDust = 2 * cantidad
        
        ashRosemary = 1 * cantidad
        swampLavander = 1 * cantidad

        mammothDill = 1 * cantidad

        caveGarlic = 1 * cantidad
        cliffRue = 1 * cantidad
        sunTarragon = 1 * cantidad
        
        queensPepper = 1 * cantidad
        
        bot.send_message(cid, f"""Not enough materials to craft crappy morph pots. @nixth @Cocytus0 @nick_the_dick
Required:
 {maccunut} x Maccunut
 {grass} x Tecceagrass
 {ashRosemary} x Ash Rosemary
 {swampLavander} x Swamp Lavender
 {mammothDill} x Mammoth Dill
 {caveGarlic} x Cave Garlic
 {queensPepper} x Queen's Pepper""")

        bot.send_message(cid, f"""Not enough materials to craft crappy morph pots. @Ale_Guetta @licuevas @nixth 
Required:
 {silverOre} x Silver Ore
 {powder} x Powder""")

def replace_request(update: Update, context: CallbackContext):
    bot = context.bot
    cid = update.message.chat_id    
    uid = update.effective_user.id
    # (?<!\n) Me aseguro que no hay lineas anteriores asi evito montruos y ambush
    # Luego tomo lo necesario.
    m = re.search('\/s\/(.*)\/(.*)', update.message.text)    
    if m != None:
        if update.message.reply_to_message != None and update.message.reply_to_message.text != "":
            bot.send_message(cid, update.message.reply_to_message.text.replace(m.group(1), m.group(2)))
        else:
            bot.send_message(cid, "Tenes que hacer reply a un mensaje para que funcione!")

def main():
    updater = Updater(REPORT_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", command_start))
    dp.add_handler(CommandHandler("melody", command_melody))
    dp.add_handler(CommandHandler("lancelot", command_lancelot))  
    dp.add_handler(CommandHandler("crappy_channels", command_channels))
    dp.add_handler(CommandHandler("paralian", command_paralian))
    dp.add_handler(CommandHandler("nixth_regala_pogs", command_nixth_regala_pogs))

    dp.add_handler(CommandHandler("help", command_help))

    dp.add_handler(MessageHandler(Filters.regex("Pot (rage|peace|morph) (\d+)"), pot_request))
    dp.add_handler(MessageHandler(Filters.regex("\/s\/(.*)\/(.*)"), replace_request))
    
    updater.start_polling(timeout=30)
    updater.idle()

if __name__ == '__main__':
    main()
