from abc import ABC, abstractmethod
from datetime import datetime
import json
import os
import pandas as pd

class Data(ABC):
    @abstractmethod
    def init_history_k(self):
        pass

    @abstractmethod
    def update_history_k(self):
        pass

    def load_data(self, config_path="config", filename="stock.json"):
        with open(os.path.join(config_path, filename), "r") as f:
            self.cfg = json.load(f)

    @staticmethod
    def get_filename_by_code(code: str) -> str:
        return f"{code}.csv"
    @staticmethod
    def get_current_date():
        return datetime.now().strftime("%Y-%m-%d")
    
    @staticmethod
    def rename_futu_table_head(ohlcv: pd.DataFrame) -> pd.DataFrame:
        """rename table head & format Date using pd.to_datetime for plotting k-line via mfp, the DataFrame contains following data:

        Args:
            ohlcv (pd.DataFrame): code,name,time_key,open,close,high,low,pe_ratio,turnover_rate,volume,turnover,change_rate,last_close

        Returns:
            pd.DataFrame: set date as index and formatted by pd.to_datetime()
        """
        # code,name,time_key,open,close,high,low,pe_ratio,turnover_rate,volume,turnover,change_rate,last_close
        new_col_names = {
            'time_key': 'Date',
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        }

        ohlcv.rename(columns=new_col_names, inplace=True)
        ohlcv['Date'] = ohlcv['Date'].apply(lambda x: x.split(' ')[0])
        ohlcv['Date'] = pd.to_datetime(ohlcv['Date'])
        ohlcv.set_index('Date', inplace=True)
        return ohlcv
