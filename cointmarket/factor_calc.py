import abc
from typing import Dict, Optional
import datetime

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import pandas as pd
from pandas import DataFrame


class FactorCalc(abc.ABC):

    @abc.abstractmethod
    def init(self, **kwargs):
        pass

    @abc.abstractmethod
    def on_dataupdate(self, symbol:str, ts:int, data_update:Dict[str, float]):
        pass

    @abc.abstractmethod
    def get_value(self, symbol:str) -> float:
        pass



class VolatilityCalc(FactorCalc):

    def __init__(self, calc_config):
        self.init(**calc_config)

    def init(self, **kwargs):
        self.symbols = kwargs['symbols']#["BTCUSDT", "ETHUSDT"]
        self.calc_field = kwargs['calc_field']#'price'
        self.window_len_secs = kwargs['window_len_secs'] #60
        self._window_str = str(self.window_len_secs) + "s"

        self.window_df_dict:Dict[str,DataFrame] = {}

        for s in self.symbols:
            self.window_df_dict[s] = pd.DataFrame({'time': [], 'value': []})


    def on_dataupdate(self, symbol:str, ts: int, data_update: Dict[str, float]):
        value = data_update[self.calc_field]
        if symbol in self.window_df_dict:
            sym_window_df = self.window_df_dict[symbol]
            ts_dt = pd.to_datetime(ts, unit='ms')
            sym_window_df = sym_window_df.append({'time': ts_dt, 'value': value}, ignore_index=True)

            first_ts_dt = sym_window_df.iloc[0]['time']

            if ts_dt - first_ts_dt > datetime.timedelta(seconds=self.window_len_secs):
                sym_window_df = sym_window_df.iloc[1:]

            self.window_df_dict[symbol] = sym_window_df


    def get_value(self, symbol:str) -> Optional[float]:
        if symbol in self.window_df_dict:
            sym_df = self.window_df_dict[symbol].set_index("time").sort_index()
            std_df = sym_df.rolling(self._window_str).std()

            return std_df.iloc[-1]['value']
        return None