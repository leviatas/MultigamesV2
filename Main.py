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
