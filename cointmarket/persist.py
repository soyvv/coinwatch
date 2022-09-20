import logging
from abc import ABC, abstractmethod
from typing import Dict

import pandas as pd
from pandas import DataFrame
import psycopg2 as pg
import datetime



class HistStore(ABC):

    @abstractmethod
    def store(self, symbol: str, ts: int, data:Dict[str,float]):
        pass


    @abstractmethod
    def close(self):
        pass


class TimescaledbHistStore(HistStore):

    def __init__(self, conn_string:str):
        self.conn_string = conn_string
        self.conn = pg.connect(self.conn_string)



    def store(self, symbol: str, ts: int, data: Dict[str, float]):
        cursor = self.conn.cursor()

        for k, v in data.items():
            table_name = "coin_" + k
            # todo: ensure table_name exist in db; otherwise may create the table first
            sql = "INSERT INTO " + table_name + "(time, symbol, value) VALUES (%s, %s, %s)"
            d = (datetime.datetime.utcfromtimestamp(ts*1.0/1000), symbol, v)
            try:
                cursor.execute(sql, d)
            except(Exception, pg.Error) as error:
                logging.error("error when persisting:")
                logging.error(error)

        self.conn.commit()


    def close(self):
        self.conn.close()
