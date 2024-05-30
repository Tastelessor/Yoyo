import os
from futu import *
import pandas as pd
from datetime import datetime

def _get_stock_filename(stock: str) -> str:
    return f"{stock}.csv"

def pull_history_k(stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
    ret, data, page_req_key = quote_ctx.request_history_kline(stock_code, start=start_date, end=end_date, max_count=30)  # 每页5个，请求第一页
    if ret != RET_OK:
        print('error:', data)
        quote_ctx.close()
        return
    print('############## start pulling k line data ################')
    while page_req_key != None:
        ret, data_follow, page_req_key = quote_ctx.request_history_kline(stock_code, start=start_date, end=end_date, max_count=30, page_req_key=page_req_key) # 请求翻页后的数据
        if ret != RET_OK:
            print('error:', data_follow)
            quote_ctx.close()
            return
        data = pd.concat([data, data_follow], axis=0)
    quote_ctx.close()
    return data

def init_history_k(stock_code: str, start_date: str, end_date: str) -> None:
    output_csv = _get_stock_filename(stock_code)
    data = pull_history_k(stock_code, start_date, end_date)
    data.to_csv(output_csv, index=False)

def _get_current_date():
    return datetime.now().strftime("%Y-%m-%d")

def update_history_k(stock_code: str) -> None:
    output_csv = _get_stock_filename(stock_code)
    if not os.path.exists(output_csv):
        print(f"No such file: {output_csv}, please init before update")
        return
    data = pd.read_csv(output_csv)
    start_date = data.iloc[-1]['time_key'].split(' ')[0]
    end_date = _get_current_date()
    print(f"Update data from {start_date} to {end_date}")
    if start_date is not end_date:
        update_data = pull_history_k(stock_code, start_date, end_date)
        if update_data is not None:
            data = data.drop(len(data) - 1) # drop the last row
            data = pd.concat([data, update_data], axis=0)
            data.to_csv(_get_stock_filename(stock_code), index=False)

# init_history_k('HK.09868', '2018-07-08', '2024-05-29')