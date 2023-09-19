from py3cw.TelegramManager import TelegramManager
from config import config
import TradingViewManager
import threading
import asyncio
import re


def main():
    try:
        #asyncio.run(TelegramManager(config['bot_token']).start_bot())
        TelegramManager(config['bot_token']).start_bot()
        '''t2 = threading.Thread(
            target=TradingViewManager.app.run(host='127.0.0.1', port=80, debug=True))
        t1 = threading.Thread(target=TelegramManager(config['bot_token']).start_bot())


        t1.start()
        t2.start()'''
    except Exception as e:
        print(e)


if __name__ == '__main__':
    #main()
    str = "cats AND*Dogs.Are Awesome"
    mystr = re.split(r'[`\-=~!@#$%^&*()_+\[\]{};\'\\:"|<,./<>?]', str)
    for a in mystr:
        x = a.split("\t")
        print(x)
    '''t2 = threading.Thread(
        target=TradingViewManager.app.run(host='127.0.0.1', port=80, debug=True))'''