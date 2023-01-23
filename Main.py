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

import functools

log.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=log.INFO)
logger = log.getLogger(__name__)


from multiprocessing import Process
""" import psutil """

def loop_c():
    while 1:
        sleep(0.01)
        MainController.main()

def loop_g():
    while 1:
        sleep(0.01)
        reportBot.main()

def loop_j():
    while 1:
        sleep(0.01)
        secretHitlerBot.main()

if __name__ == '__main__':
    # Multigames
    p3 = Process(target=loop_c).start()
    # Report Bot
    p7 = Process(target=loop_g).start()
    # Secret Hitler
    p8 = Process(target=loop_j).start()