#!/usr/bin/env python

import os, certifi  # win32api

import time
import logging
from binance.lib.utils import config_logging
from binance.websocket.spot.websocket_client import SpotWebsocketClient as Client

config_logging(logging, logging.DEBUG)


def message_handler(message):
    logging.info(message)


os.environ['SSL_CERT_FILE'] = certifi.where()

my_client = Client(stream_url="wss://testnet.binance.vision")
#my_client = Client()
my_client.start()

# Live subscription
my_client.ticker(
    symbol="bnbusdt",
    id=1,
    callback=message_handler,
)

# Combined subscription
my_client.instant_subscribe(
    ["btcusdt@ticker", "ethusdt@ticker"], callback=message_handler
)

time.sleep(2000)

logging.debug("closing ws connection")
my_client.stop()