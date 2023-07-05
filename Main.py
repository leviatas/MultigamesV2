import configparser
import os
#import socks
from telethon import TelegramClient, events, types, functions, Button
import logging as log
import asyncio
from time import sleep
from telethon.sessions import StringSession

import MainController
import reportBot.main as reportBot
import SecretHitler.MainController as secretHitlerBot
import BloodClocktower.Controller as bloodClocktowerBot
import discordBot.main as discordBot

import functools
import requests

log.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s MultigamesV2',
    level=log.INFO)
logger = log.getLogger(__name__)


from multiprocessing import Process
""" import psutil """

def loop_a():
    while 1:
        sleep(0.01)
        MainController.main()

def loop_b():
    while 1:
        sleep(0.01)
        reportBot.main()

def loop_c():
    while 1:
        sleep(0.01)
        secretHitlerBot.main()

def loop_d():
    while 1:
        sleep(0.01)
        bloodClocktowerBot.main()

def loop_e():
    while 1:
        sleep(0.01)
        discordBot.run()

if __name__ == '__main__':
    # Multigames
    p1 = Process(target=loop_a).start()
    # Report Bot
    p2 = Process(target=loop_b).start()
    # Secret Hitler
    p3 = Process(target=loop_c).start()
    #bot on the clocktower
    p4 = Process(target=loop_d).start()
    #bot de discord
    p5 = Process(target=loop_e).start()

    # Verificador que el proceso de multigames siga activo
    while 1:
        sleep(1)
        if not p1.is_alive():
            report_bot_token = os.environ.get('TOKEN_REPORT', None)
            report_chat_id = os.environ.get('CHAT_REPORT', None)
            x = requests.get(f'https://api.telegram.org/bot{report_bot_token}/sendMessage?chat_id=-{report_chat_id}&text=ERROR:%20Multigames2Bot:%20{p1.exitcode}')
            # Si el proceso no esta vivo entonces lo revivo 
            p1 = Process(target=loop_a).start()
