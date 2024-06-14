import os
import json
import pandas as pd
from futu import *
from datetime import datetime
from YoyoLogger import logger
from YoyoData.Data import Data

class StockData(Data):
    def __init__(self) -> None:
        pass

    def pull_history_k(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
        ret, data, page_req_key = quote_ctx.request_history_kline(stock_code, start=start_date, end=end_date, max_count=30)  # 每页5个，请求第一页
        if ret != RET_OK:
            logger.info('error:', data)
            quote_ctx.close()
            return
        logger.info('############## start pulling k line data ################')
        while page_req_key != None:
            ret, data_follow, page_req_key = quote_ctx.request_history_kline(stock_code, start=start_date, end=end_date, max_count=30, page_req_key=page_req_key) # 请求翻页后的数据
            if ret != RET_OK:
                logger.info('error:', data_follow)
                quote_ctx.close()
                return
            data = pd.concat([data, data_follow], axis=0)
        quote_ctx.close()
        return data
    
    def ohclv_to_datetime(self, ohclv: pd.DataFrame) -> None:
        ohclv['time_key'] = pd.to_datetime(ohclv['time_key'])
        ohclv['date'] = ohclv['time_key'].dt.strftime('%Y-%m-%d')

    def export_to_csv(self, data: pd.DataFrame, stock_code: str) -> None:
        data.to_csv(Data.get_filename_by_code(stock_code), index=False, index_label='date')

    def init_history_k(self, stock_code: str, start_date: str, end_date: str) -> None:
        data = self.pull_history_k(stock_code, start_date, end_date)
        self.ohclv_to_datetime(data)
        self.export_to_csv(data, stock_code)

    def update_history_k(self, stock_code: str) -> None:
        output_csv = Data.get_filename_by_code(stock_code)
        if not os.path.exists(output_csv):
            logger.info(f"No such file: {output_csv}, please init before update")
            return
        data = pd.read_csv(output_csv)
        start_date = data.iloc[-1]['time_key'].split(' ')[0]
        end_date = Data.get_current_date()
        logger.info(f"Update data from {start_date} to {end_date}")
        if start_date is not end_date:
            update_data = self.pull_history_k(stock_code, start_date, end_date)
            self.ohclv_to_datetime(update_data)
            if update_data is not None:
                data = data.drop(len(data) - 1) # drop the last row
                data = pd.concat([data, update_data], axis=0)
                self.export_to_csv(data, stock_code)

    @staticmethod
    def get_stock_dataframe(stocks: list[str]) -> dict:
        res = dict()
        logger.info(stocks)
        for stock_code in stocks:
            logger.info(f"loading data for {stock_code}")
            output_csv = Data.get_filename_by_code(stock_code)
            if not os.path.exists(output_csv):
                logger.error(f"No such file: {output_csv}, please init before update")
                continue
            res[stock_code] = pd.read_csv(output_csv)
        return res

# sd = StockData()
# sd.init_history_k('HK.09866', '2022-03-14', '2024-06-13')
# sd.init_history_k('HK.02015', '2021-08-12', '2024-06-13')