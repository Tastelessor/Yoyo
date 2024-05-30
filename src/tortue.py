import os
import pandas as pd
from typing import Union
from data import _get_stock_filename
from draw import draw_k_line, show_plot, draw_asset_line
import numpy as np

# code, name, time_key, open, close, high, low, pe_ratio, turnover_rate, volume, turnover, change_rate, last_close
def _get_data_frame(stock_code: str, name_list: list[str] = []) -> pd.DataFrame:
    data = pd.read_csv(_get_stock_filename(stock_code))
    if len(name_list) == 0:
        return data
    return data.loc[:, name_list]

def _cal_price(ohlcv: pd.Series, threshold: float) -> float:
    return (ohlcv['high'] + ohlcv['low']) * 0.5

def _cal_asset(balance: float, stock_amount: int, close: float) -> float:
    return balance + stock_amount * close

def sell(trade_cfg: dict, price: float) -> int:
    sell_amount = 0
    if trade_cfg['shares_amount'] > 0:
        if trade_cfg['shares_amount'] < trade_cfg['trade_unit']:
            sell_amount = trade_cfg['shares_amount']
        else:
            sell_amount = trade_cfg['trade_unit']
        trade_cfg['whole_money'] += price * sell_amount * (1 - trade_cfg['tax'])
        trade_cfg['shares_amount'] -= sell_amount
    return sell_amount * -1

def buy(trade_cfg: dict, price: float) -> int:
    buy_amount = 0
    if trade_cfg['whole_money'] > trade_cfg['trade_unit'] * price:
        buy_amount = trade_cfg['trade_unit']
    else:
        buy_amount = trade_cfg['whole_money'] / price
        buy_amount = buy_amount - buy_amount % trade_cfg['minimun_hand']
    trade_cfg['whole_money'] -= price * buy_amount * (1 + trade_cfg['tax'])
    trade_cfg['shares_amount'] += buy_amount
    return buy_amount

def after_a_day(trade_cfg: dict, day_record: pd.Series) -> tuple[int, float]:
    """exec buy & sell strategy in a day

    Args:
        trade_cfg (dict): check find_the_best_sell_buy()
        day_record (pd.Series): a row: code,name,time_key,open,close,high,low,pe_ratio,turnover_rate,volume,turnover,change_rate,last_close

    Returns:
        int: transcation amount
        float: transcated price
    """
    price = 0.0
    transc_func = None

    if day_record['change_rate'] < trade_cfg['sell_threshold']:
        price = _cal_price(day_record, trade_cfg['sell_threshold'])
        transc_func = sell

    elif day_record['change_rate'] > trade_cfg['buy_threshold']:
        price = _cal_price(day_record, trade_cfg['buy_threshold'])
        transc_func = buy

    if transc_func:
        return transc_func(trade_cfg, price), price
    return tuple([None, None])


def find_the_best_sell_buy(stock_code: str, sell_threshold: list[float], buy_threshold: list[float]) -> list[dict]:
    data = _get_data_frame(stock_code)
    results = []
    for sell_rate in range(sell_threshold[0], sell_threshold[1], 1):
        for buy_rate in range(buy_threshold[0], buy_threshold[1], 1):
            for trade_unit in range(5000, 50001, 5000):
                trade_cfg = {
                    'whole_money': 100000,
                    'trade_unit': trade_unit,
                    'sell_threshold': sell_rate,
                    'buy_threshold': buy_rate,
                    'carry_cost': 0,
                    'shares_amount': 0,
                    'tax': 0.001,
                    'minimun_hand': 100
                }
                print(f"############# For sell: {sell_rate}, buy: {buy_rate}, trade unit: {trade_unit} #################")
                if sell_rate > buy_rate:
                    continue
                buy_records = []
                sell_records = []
                asset_records = []
                for _, row in data.iterrows():
                    amount, price = after_a_day(trade_cfg, row)
                    asset_records.append({'date': row['time_key'], 
                                             'asset': _cal_asset(trade_cfg['whole_money'], trade_cfg['shares_amount'], row['close']) / 10000.0})
                    if amount is not None:
                        if amount > 0:
                            buy_records.append({'date': row['time_key'], 'price': price})
                        elif amount < 0:
                            sell_records.append({'date': row['time_key'], 'price': price})
                trade_cfg['whole_money'] = int(trade_cfg['whole_money'])
                trade_cfg['total_value'] = int(trade_cfg['whole_money'] + trade_cfg['shares_amount'] * 39.05)
                trade_cfg['buy_records'] = buy_records
                trade_cfg['sell_records'] = sell_records
                trade_cfg['asset_records'] = asset_records
                results.append(trade_cfg)
    results = sorted(results, key=lambda item: item['total_value'])
    for item in results:
        item['in_w'] = f"{item['total_value'] / 10000}w" 
    return results

# results = find_the_best_sell_buy('HK.09866', [-10, 10], [-10, 10])
stock_code = 'HK.02015'
results = find_the_best_sell_buy(stock_code, [0, 1], [5, 6])
best = results[-1]
buy_records = best.pop('buy_records')
sell_records = best.pop('sell_records')
asset_records = best.pop('asset_records')
fig = draw_k_line(stock_code, buy_records, sell_records)
draw_asset_line(fig, asset_records)
df = pd.DataFrame(buy_records)
df.to_csv(f"buy_buy_{best['buy_threshold']}_{best['sell_threshold']}.csv", index=False)
df = pd.DataFrame(sell_records)
df.to_csv(f"sell_buy_{best['buy_threshold']}_{best['sell_threshold']}.csv", index=False)
print(best)
print(f"I won ${best['whole_money'] / 10000.0}w, and I hold {best['shares_amount']} stocks")
show_plot()
# df = pd.DataFrame(results)
# df.to_csv('results.csv', index=False)