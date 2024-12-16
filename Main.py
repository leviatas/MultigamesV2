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
import resource


log.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s MultigamesV2',
    level=log.INFO)
logger = log.getLogger(__name__)


from multiprocessing import Process
""" import psutil """

def run_loop(target_function):
    """Reusable loop to repeatedly call a target function with a sleep interval."""
    while True:
        try:
            sleep(0.01)
            target_function()
        except Exception as e:
            logger.error(f"An error occurred in {target_function.__name__}: {e}")

def memory_limit(percentage: float):
    """Limit max memory usage to half."""
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    # Convert KiB to bytes, and divide in two to half
    resource.setrlimit(resource.RLIMIT_AS, (get_memory() * 1024 * percentage, hard))

def get_memory():
    with open('/proc/meminfo', 'r') as mem:
        free_memory = 0
        for i in mem:
            sline = i.split()
            if str(sline[0]) in ('MemFree:', 'Buffers:', 'Cached:'):
                free_memory += int(sline[1])
    return free_memory

if __name__ == '__main__':
    functions = [
        ("MainController", MainController.main),
        #("reportBot", reportBot.main),
        ("secretHitlerBot", secretHitlerBot.main),
        ("bloodClocktowerBot", bloodClocktowerBot.main),
        #("discordBot", discordBot.run)
    ]

    #memory_limit(0.9)
    processes = []
    for name, func in functions:
        p = Process(target=run_loop, args=(func,), name=f"Process-{name}")
        p.start()
        processes.append(p)

    # Verificador que el proceso de multigames siga activo
    # while 1:
    #     sleep(1)
    #     if not p1.is_alive():
    #         report_bot_token = os.environ.get('TOKEN_REPORT', None)
    #         report_chat_id = os.environ.get('CHAT_REPORT', None)
    #         x = requests.get(f'https://api.telegram.org/bot{report_bot_token}/sendMessage?chat_id=-{report_chat_id}&text=ERROR:%20Multigames2Bot:%20{p1.exitcode}')
    #         # Si el proceso no esta vivo entonces lo revivo 
    #         p1 = Process(target=loop_a).start()
