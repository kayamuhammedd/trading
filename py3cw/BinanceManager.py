import json
import pandas as pd
from binance.client import Client as binanceClient
from config import config

from DbManager import DBHelper

class BinanceManager:
    def __init__(self):
        self.api_key = "w9aYHSBTXnclcy3c4YatGmzthBbGT4u9DdQUgeBPhr1MwmCiCsqVcIm60Ga5cyhP"
        self.api_secret = "teDT2AAk8hcWByaLt6aHX0wEWUthoL9VvDMmQXaqjKLXLUaI5w8S1VlfOaVM1PEU"
        self.client = binanceClient(self.api_key, self.api_secret)
        #self.bsm = BinanceSocketManager(self.client)
        #self.conn = self.bsm.start_symbol_ticker_futures_socket('XLMUSDT', self.trade_history)
        #self.bsm.start()
        self.btc_price = {'error': False}
        self.DB = DBHelper()



    def get_last_price_of_symbol(self, symbol):
        print("price =", binanceClient.get_ticker(symbol))
        return binanceClient.get_ticker(symbol)['lastPrice']

    def get_balance(self):
        balance = self.client.futures_account_balance()
        self.client.get
        return balance

    def get_futures_info(self):

        #trx_futures_price = self.client.futures_symbol_ticker(symbol="TRXUSDT")
        #futures_info  = self.client.futures_position_information(symbol='KAVAUSDT')
        open_futures = self.client.futures_get_open_orders()
        #futures = self.client.futures_account()
        #print(futures)
        print(open_futures)
        return open_futures

    def SendBuyRequest(self, symbol, quantity, buyPrice):
        try:
            binanceClient.order_limit_buy(symbol=symbol, quantity=quantity, price=buyPrice)
        except Exception as e:
            print(e)

    '''def historical_klines(self):
        # valid intervals - 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
        timestamp = self.client._get_earliest_valid_timestamp('BTCUSDT', '1d')
        try:
            bars = self.client.get_historical_klines(start_str=timestamp,symbol='BTCUSDT', interval='1d', limit=1000)
        except Exception as e:
            print(e)
        for line in bars:
            del line[5:]
        btc_df = pd.DataFrame(bars, columns=['date', 'open', 'high', 'low', 'close'])
        btc_df.set_index('date')
        #print(btc_df.head())
        btc_df.to_csv('btc_bars3.csv')
        #btc_df = pd.read_csv('btc_bars3.csv', index_col=0)
        #btc_df.index = pd.to_datetime(btc_df.index, unit='ms')
        btc_df['20sma'] = btc_df.close.rolling(20).mean()
        print(btc_df.tail(5))
        try:
            sma = btalib.sma(btc_df.close)
        except Exception as e:
            print(e)
        print(sma.df)'''

    def trade_history(self,msg):
        ''' define how to process incoming WebSocket messages '''
        if msg['e'] != 'error':
            print(msg['c'])
            self.btc_price['last'] = msg['c']
            self.btc_price['bid'] = msg['b']
            self.btc_price['last'] = msg['a']
        else:
            self.btc_price['error'] = True