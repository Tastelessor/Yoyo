from YoyoData import StockData
from YoyoLogger import logger
from YoyoStrategy import CWD
from .Strategy import TradeAction, Strategy
from .StrategyTurtle import StrategyTurtle
from .utils import *
import pandas as pd

class StrategyManager(Strategy):
    def __init__(self, stocks: list[str]=[]):
        self.bt_full_period = False
        self.strategies = {}
        self.bt_result = {}
        super().load_config(cfg=f"{CWD}/strategy_manager.json")
        self.ohclvs = StockData.get_stock_dataframe(stocks)
        

    def get_all_strategies_name(self):
        return list(self.strategies.keys())
    
    def register_strategy(self, name: str, strategy: Strategy) -> None:
        self.strategies[name] = strategy

    def execute_trade(self, ohclv: pd.Series, strategies: list[str]) -> TradeAction:
        signals = []
        for strategy_name in strategies:
            strategy = self.strategies[strategy_name]
            if strategy is None:
                logger.warning(f"Strategy [{strategy_name}] not found")
                strategies.remove(strategy)
                continue
            signals.append(strategy.execute_trade(ohclv))
        return sum(signals, start=TradeAction.HOLD)

    def execute_strategy(self, stocks: list[str], strategy: str) -> TradeAction:
        res = {}
        strategy = self.strategies.get(strategy)
        if strategy is None:
            raise ValueError("Strategy not found")
        for stock in stocks:
            res[stock] = strategy.execute_trade(self.ohclvs[stock])
        return res
        
    def execute_strategies(self, stocks: list[str], strategies: list[str]) -> TradeAction:
        signals = {}
        for stock in stocks:
            for strategy_name in strategies:
                strategy = self.strategies[strategy_name]
                if strategy is None:
                    logger.warning(f"Strategy [{strategy_name}] not found")
                    strategies.remove(strategy)
                    continue
                logger.debug(f"Executing strategy: {strategy_name}, stock: {stock}")
                signals[stock] = strategy.execute_trade(self.ohclvs[stock])
        return signals
    
    def clear_registered_strategies(self):
        self.strategies = {}

    def back_test_load_test_cfg(self):
        bt_cfg = self.cfg.get("back_test")
        # asset & trading configs
        self.bt_capital = bt_cfg.get("initial_capital")
        self.bt_commission = bt_cfg.get("commission")
        self.bt_tax = bt_cfg.get("tax")
        self.extra_cost = self.bt_tax + self.bt_commission
        self.trade_units = bt_cfg.get("trade_unit")
        self.min_trade_unit = bt_cfg.get("min_trade_unit")

        # period for testing, if not configured, means running for all data
        if bt_cfg.get("full_period") is True:
            self.bt_full_period = True
        else:
            self.bt_start_date = bt_cfg.get("start_date")
            self.bt_end_date = bt_cfg.get("end_date")
            period = bt_cfg.get("period")
            if period is not None and period > 0:
                self.bt_end_date = after_n_days(self.bt_start_date, period)

        self.bt_test_comb = []
        strategy_set = set()
        # back test combinations for all stocks configured in [stocks] and corresponding strategies
        for test_combination in bt_cfg.get("test_combinations"):
            self.bt_test_comb.append({
                "stock_code": test_combination.get("stock_code"),
                "strategy": test_combination.get("strategy"),
            })
            strategy_set.add(*test_combination.get("strategy"))
            
        # composite param combinations for all strategies configured in [test_combination], the name must match
        s_params = bt_cfg.get("strategy_params")
        if bt_cfg.get("use_strategy_cfg") == True:
            self.bt_strategy_comb = {} # init back test strategy combinations
            for strategy in strategy_set:
                logger.info(f"Loading strategy [{strategy}] parameters...")
                self.bt_strategy_comb[strategy] = {}
                for key, vals in s_params.get(strategy).items():
                    logger.info(f"Loading strategy [{strategy}] parameter [{key}]...")
                    self.bt_strategy_comb[strategy][key] = params_product(s_params.get("param_stride"), vals)
        else:
            # TODO: load strategy_cfg
            pass

    def back_test_sort_result(self) -> None:
        for stock, result in self.bt_result.items():
            self.bt_result[stock] = sorted(result, key=lambda x: x["bt_result"]["capital"], reverse=True)

    def back_test_export_result(self) -> None:
        for stock, result in self.bt_result.items():
            result_list = []
            for dict_data in result:
                merge_dict = {}
                for key, inner_dict in dict_data.items():
                    merge_dict.update(inner_dict)
                result_list.append(merge_dict)
            df = pd.DataFrame(result_list)
            df.to_csv(f"{CWD}/backtest_result/bt_{stock}.csv", index=False)

    def back_test_after_one_day(self, bt_st: dict, ohclv: pd.Series, signal: TradeAction, date: str) -> None:
        price = (ohclv['high'] + ohclv['low']) * 0.5
        # logger.debug(f"{date}: capital: {round(bt_st["capital"], 2)}, balance: {round(bt_st['balance'], 2)}, shares: {bt_st['shares']}")
        if signal == TradeAction.HOLD:
            bt_st["capital"] = bt_st["balance"] + bt_st["shares"] * ohclv['close']
            bt_st["capital_records"].append(bt_st["capital"])
            return
        # calculate cost
        trade_unit = self.trade_unit
        if signal == TradeAction.BUY:
            asset_change = price * (1 + self.extra_cost)
            cost = trade_unit * asset_change
            if bt_st["balance"] < cost:
                trade_unit = (bt_st["balance"] / asset_change) // self.min_trade_unit * self.min_trade_unit
                if trade_unit < self.min_trade_unit:
                    cost = 0
                else:
                    cost = trade_unit * asset_change
            if cost != 0:
                # logger.debug(f"{date}: {signal} {trade_unit}, -{cost}")
                bt_st["shares"] += trade_unit
                bt_st["balance"] -= cost
                bt_st["buys"].append(date)
        elif signal == TradeAction.SELL:
            asset_change = price * (1 - self.extra_cost)
            income = trade_unit * asset_change
            if bt_st["shares"] < self.trade_unit:
                trade_unit = bt_st["shares"]
                income = trade_unit * asset_change
            if income != 0:
                # logger.debug(f"{date}: {signal} {trade_unit}, +{income}")
                bt_st["shares"] -= trade_unit
                bt_st["balance"] += income
                bt_st["sells"].append(date)        
        # update capital
        bt_st["capital"] = bt_st["balance"] + bt_st["shares"] * ohclv['close']
        bt_st["capital_records"].append(bt_st["capital"], 2)

    def back_test_run(self, ohclv: pd.DataFrame) -> dict:
        bt_statistic = {
            "capital": self.bt_capital,
            "trade_unit": self.trade_unit,
            "balance": self.bt_capital,
            "shares": 0,
            "capital_records": [], 
            "buys": [],
            "sells": []
        }

        for ohclv_day in ohclv.iterrows():
            # it's a tuple of {date, data} due to the date index
            signal = self.execute_trade(ohclv_day[1], self.get_all_strategies_name())
            self.back_test_after_one_day(bt_statistic, ohclv_day[1], signal, ohclv_day[0])
        bt_statistic["capital"] = round(bt_statistic["capital"], 2)
        return bt_statistic

    def back_test(self):
        if self.bt_strategy_comb is None:
            logger.critical("Load backtesting configuration first!")
        for test_combination in self.bt_test_comb:
            stocks = test_combination.get("stock_code")
            self.ohclvs = StockData.get_stock_dataframe(stocks)
            strategies = test_combination.get("strategy")
            comb_list = strategy_product(self.bt_strategy_comb)
            for stock in stocks:
                logger.debug(f"Back testing stock [{stock}]...")
                self.cur_stock = stock
                self.bt_result[stock] = []
                for strategy_comb in comb_list: # use a strategy combination on a stock
                    logger.debug(f"Strategy combination: {strategy_comb}")
                    self.clear_registered_strategies()
                    for strategy in strategies: # register strategies for one back test
                        strategy_class = globals()[strategy]
                        strategy_instance = strategy_class(strategy_comb.get(strategy))
                        # dynamic initializing a strategy class, eval is unsafe but can be used for debugging
                        # strategy_instance = eval(f"{strategy}({strategy_comb.get(strategy)})")
                        self.register_strategy(strategy, strategy_instance)
                    for trade_unit in range(*self.trade_units):
                        self.trade_unit = trade_unit
                        ohclv = self.ohclvs.get(stock)
                        if self.bt_full_period is False:
                            while ohclv.index.__contains__(self.bt_start_date):
                                self.bt_start_date = after_n_days(self.bt_start_date, 1)
                            while ohclv.index.__contains__(self.bt_end_date):
                                self.bt_end_date = after_n_days(self.bt_end_date, 1)
                            ohclv = ohclv.loc[self.bt_start_date : self.bt_end_date]
                        # get back test statistic result
                        self.bt_result[stock].append({
                            "strategy_combination": strategy_comb,
                            "bt_result": self.back_test_run(ohclv)
                        })


        

# stocks = ['HK.09866']
# strategies = ['turtle']
sm = StrategyManager()
# sm.register_strategy("turtle", StrategyTurtle())
# sm.execute_strategy(stocks, 'turtle')
sm.back_test_load_test_cfg()
sm.back_test()
sm.back_test_sort_result()
sm.back_test_export_result()