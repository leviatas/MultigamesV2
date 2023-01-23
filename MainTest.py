
import os

import logging as log
from time import sleep
# import MainController
# import reportBot.main as reportBot
import SecretHitler.MainController as secretHitlerBot

from multiprocessing import Process

log.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=log.INFO)
logger = log.getLogger(__name__)

# def loop_c():
#     while 1:
#         sleep(0.01)
#         MainController.main()

# def loop_g():
#     while 1:
#         sleep(0.01)
#         reportBot.main()

def loop_j():
    while 1:
        sleep(0.01)
        secretHitlerBot.main()

if __name__ == '__main__':
    # for name, value in os. environ. items():
    #     print("{0}: {1}". format(name, value))
    # Multigames
    # p3 = Process(target=loop_c).start()
    # Report Bot
    # p7 = Process(target=loop_g).start()
    # Secret Hitler
    p8 = Process(target=loop_j).start()