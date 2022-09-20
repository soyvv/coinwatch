import streamlit as st
import pandas as pd
import numpy as np
import psycopg2 as pg
import zerorpc
import logging
import time
import warnings
import os



from config import ConfigClient, config_profiles, EnvConfig

warnings.simplefilter(action='ignore', category=UserWarning)
from pandas import DataFrame

import plotly.graph_objects as go

ENV =  os.environ ['COIN_WATCH_ENV'] if 'COIN_WATCH_ENV' in os.environ else 'dev'
if ENV is None:
    ENV = 'dev'

st.title("Coin Watch Dashboard")


@st.experimental_singleton
def get_watch_config(_mongo_url:str):
    config_client = ConfigClient(_mongo_url)
    return config_client


@st.experimental_singleton
def get_env_config(_env:str):
    env_config = config_profiles[_env]
    return env_config

data = {}



## todo: fix this
_rpc_client = None
# _db_conn = None

#@st.experimental_singleton
def rpc_client(_rpc_addr) -> zerorpc.Client:
    global _rpc_client
    if _rpc_client is None:
        logging.debug("creating rpc client")
        print("creating rpc client")
        _rpc_client = zerorpc.Client()
        _rpc_client.connect(_rpc_addr)
    return _rpc_client

@st.experimental_singleton
def db_conn(_pg_url):
    _db_conn = pg.connect(_pg_url)
    return _db_conn


def get_data(env_config) :
    rpc = rpc_client(env_config.zerorpc_client_addr)
    mkt_snapshot = rpc.query()
    logging.debug(mkt_snapshot)
    for data_item in mkt_snapshot.values():
        sym = data_item['s']
        if sym not in data:
            data[sym] = {}
        data[sym].update(data_item['data'])

    tsdb_conn = db_conn(env_config.pg_url)
    ohlc_data = get_ohlc_data(tsdb_conn)

    for sym,v in data.items():
        sym_ohlc = ohlc_data[ohlc_data['symbol']==sym]
        data[sym]['hist'] = sym_ohlc

    return data



_candle_stick_sql = '''
    SELECT
    time_bucket('1 min', time) AS bucket,
    symbol,
    FIRST(value, time) AS "open",
    MAX(value) AS high,
    MIN(value) AS low,
    LAST(value, time) AS "close"
    FROM coin_price
    WHERE time > NOW() - INTERVAL '1 hours'
    GROUP BY bucket, symbol
    '''

def get_ohlc_data(conn):
    ohlc_data = pd.read_sql(_candle_stick_sql, conn)
    return ohlc_data



def create_candlestick_chart(ohlc_data:DataFrame):
    fig = go.Figure(data=[go.Candlestick(x=ohlc_data['bucket'],
                                         open=ohlc_data['open'],
                                         high=ohlc_data['high'],
                                         low=ohlc_data['low'],
                                         close=ohlc_data['close'])
                          ])

    return fig



def dashboard_main():
    placeholder = st.empty()

    env_config = get_env_config(ENV)
    watch_config = get_watch_config(env_config.mongo_url)

    while True:
        data = get_data(env_config)
        with placeholder.container():
            for sym, sym_data in data.items():
                with st.container():
                    st.header(sym)
                    price, vol = st.columns([4,4])
                    price.metric("Fair Price", sym_data['price'])
                    vol.metric("Volatility", sym_data['volatility'])
                    #chart.line_chart(sym_data['hist'])
                    fig = create_candlestick_chart(sym_data['hist'])
                    st.plotly_chart(fig)
            time.sleep(watch_config.get_config().update_interval)


dashboard_main()

