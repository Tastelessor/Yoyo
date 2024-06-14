from YoyoData import StockData
from YoyoLogger import logger
from YoyoStrategy import TradeAction, Strategy, StrategyTurtle, CWD
from utils import *

class StrategyManager(Strategy):
    def __init__(self, stocks: list[str]=[]):
        self.strategies = {}
        self.bt_full_period = False
        super().load_config(cfg=f"{CWD}/strategy_manager.json")
        self.ohclvs = StockData.get_stock_dataframe(stocks)

    def register_strategy(self, name, strategy: Strategy):
        self.strategies[name] = strategy

    def execute_trade():
        pass

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
                logger.debug(f"Executing strategy: {strategy_name}")
                signals[stock] = strategy.execute_trade(self.ohclvs[stock])
        return signals

    def back_test_load_test_cfg(self):
        bt_cfg = self.cfg.get("back_test")
        # asset & trading configs
        self.bt_capital = bt_cfg.get("initial_capital")
        self.bt_commission = bt_cfg.get("commission")
        self.bt_tax = bt_cfg.get("tax")

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
                self.bt_strategy_comb[strategy] = {}
                for key, vals in s_params.get(strategy).items():
                    self.bt_strategy_comb[strategy][key] = dict_product(s_params.get("param_stride"), vals)
        else:
            pass

    def back_test(self):
        if self.bt_strategy_comb is None:
            logger.critical("Load backtesting configuration first!")
        

# stocks = ['HK.09866']
# strategies = ['turtle']
sm = StrategyManager()
# sm.register_strategy("turtle", StrategyTurtle())
# sm.execute_strategy(stocks, 'turtle')
sm.back_test_load_test_cfg()