
import time
import logging
import signal
import sys, os, certifi
from typing import List, Any, Dict

import zerorpc
from binance.lib.utils import config_logging
from binance.websocket.spot.websocket_client import SpotWebsocketClient as WSClient

from config import WatchConfig, EnvConfig, ConfigClient, config_profiles
from factor_calc import FactorCalc, VolatilityCalc
from persist import HistStore, TimescaledbHistStore

config_logging(logging, logging.DEBUG)




class CoinMarketWatch:
    def __init__(self, watch_config:WatchConfig, env_config:EnvConfig,  persistor:HistStore):
        self.config = watch_config
        self.persist_handler = persistor
        self.bn_client = WSClient(stream_url=env_config.md_stream_url)
        self.market_snapshot = {}  # symbol -> {val-name : val}
        self.factor_snapshot = {}  # symbol ->

        self.symbol_sub = [s.lower() + "@ticker" for s in self.config.symbols]

        logging.info("subscription: " + str(self.symbol_sub))

        self.factor_calc:Dict[str,FactorCalc] = {
            'volatility': VolatilityCalc({'symbols': self.config.symbols,
                                          'calc_field': 'price',
                                          'window_len_secs': self.config.calc_window})}


    def start(self):
        self.bn_client.start()
        self.bn_client.instant_subscribe(self.symbol_sub, callback=self._on_tick)


    def stop(self):
        self.bn_client.stop()
        self.persist_handler.close()


    def get_market_snapshot(self) -> Dict[str, Any]:
        return self.market_snapshot


    def _on_tick(self, data):
        '''
        :param tick: sample:
            {'stream': 'bnbusdt@ticker',
             'data':
                {'e': '24hrTicker', 'E': 1663401838250,
                's': 'BNBUSDT', 'p': '3.40000000', 'P': '1.244', 'w': '270.47109847', 'x': '273.50000000', 'c': '276.70000000', 'Q': '10.63000000', 'b': '276.70000000', 'B': '0.39000000', 'a': '276.80000000', 'A': '10.08000000', 'o': '273.30000000', 'h': '278.40000000', 'l': '97.90000000', 'v': '17540.20000000', 'q': '4744117.16130000', 'O': 1663315424947, 'C': 1663401824947, 'F': 50030, 'L': 53281, 'n': 3252}}
        :return:
        '''
        tick = data['data']
        symbol = tick['s']
        timestamp = (int)(tick['E'])
        bid_price = (float)(tick['b'])
        ask_price = (float)(tick['a'])
        bid_qty = (float)(tick['B'])
        ask_qty = (float)(tick['A'])

        fair_price =  (bid_price * bid_qty +ask_price * ask_qty) / (bid_qty + ask_qty)

        update = {'price': fair_price}
        self._update_snapshot(symbol, timestamp, update)
        self._update_calc(symbol, timestamp, update)
        self.persist_handler.store(symbol, timestamp, update)

        logging.debug(self.market_snapshot)


    def _update_snapshot(self, symbol, ts, data):

        #logging.debug('tick(s={}, ts={}, val={})'.format(symbol, ts, data))
        if symbol not in self.market_snapshot:
            self.market_snapshot[symbol] = {'s':symbol, 'ts': ts, 'data': {}}
        self.market_snapshot[symbol]['ts'] = ts
        self.market_snapshot[symbol]['data'].update(data)

    def _update_calc(self, symbol:str, timestamp:int, update:Dict[str,float]):
        for k, factor in self.factor_calc.items():
            factor.on_dataupdate(symbol, timestamp, data_update=update)
            val = factor.get_value(symbol)
            self.market_snapshot[symbol]['data'][k] = val


class MarketSnapshot:
    def __init__(self, market_watcher:CoinMarketWatch):
        self.market_watch = market_watcher

    def query(self):
        data_dict = self.market_watch.get_market_snapshot()
        return data_dict



def main():
    os.environ['SSL_CERT_FILE'] = certifi.where()

    env = os.environ ['COIN_WATCH_ENV'] if 'COIN_WATCH_ENV' in os.environ else 'dev'

    env_config = config_profiles[env]

    hist_store = TimescaledbHistStore(env_config.pg_url)

    config = ConfigClient(env_config.mongo_url).get_config()

    logging.info("applying watch config: ")
    logging.info(config)

    coin_mkt = CoinMarketWatch(config, env_config, hist_store)
    coin_mkt.start()

    rpc_server = zerorpc.Server(MarketSnapshot(coin_mkt))

    rpc_server.bind(env_config.zerorpc_server_addr)
    rpc_server.run()




if __name__ == "__main__":
    main()








