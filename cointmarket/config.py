from typing import List, Optional

from pymongo import MongoClient
from collections import namedtuple
import logging

WatchConfig = namedtuple('WatchConfig', ['symbols', 'update_interval', 'calc_window'])


class ConfigClient:
    def __init__(self, mongo_url):
        self.mongo_client = MongoClient(mongo_url)


    def get_config(self) -> Optional[WatchConfig]:
        db = self.mongo_client.coinwatch
        config_collection = db.coinwatch_config
        config_doc = config_collection.find_one()
        if config_doc is not None:
            config = WatchConfig(symbols=config_doc['symbols'],
                               update_interval=config_doc['update_interval'],
                               calc_window=config_doc['calc_window'])
            #logging.info("applying watch config: ")
            return config
        else:
            return None

class EnvConfig:
    md_stream_url="wss://testnet.binance.vision"
    zerorpc_server_addr = "tcp://0.0.0.0:4243"

class DevConfig(EnvConfig):
    pass


class DockerEnvConfig(EnvConfig):
    pg_url = "postgres://postgres:pass123@tsdb:5432/coinwatch"
    mongo_url = "mongodb://mongo:27017"
    zerorpc_client_addr="tcp://coinwatch-server:4243"


config_profiles = {
    'dev': DevConfig,
    'docker': DockerEnvConfig
}