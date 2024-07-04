import os
from YoyoStrategy import Strategy, TradeAction, CWD
from YoyoLogger import logger
import pandas as pd

class StrategyTurtle(Strategy):
    def __init__(self, cfg: dict=None) -> None:
        self.day = 0
        if cfg is None:
            super().load_config(__class__.__name__, f'{CWD}/strategy_cfg.json')
        else:
            self.cfg = cfg
    
    def get_trade_func_by_factor(self, factor:str):
        operator = None
        if factor.endswith('above'):
            operator = lambda x, y: x > y
        elif factor.endswith('below'):
            operator = lambda x, y: x < y
        else:
            raise ValueError(f'Invalid factor: {factor}')

        if factor.startswith('buy'):
            def buy_func(x, y):
                return TradeAction.BUY if operator(x, y) else TradeAction.HOLD
            return buy_func
        elif factor.startswith('sell'):
            def sell_func(x, y):
                return TradeAction.SELL if operator(x, y) else TradeAction.HOLD
            return sell_func
        else:
            raise ValueError(f'Invalid factor: {factor}')

    def execute_trade(self, ohclv: pd.Series) -> TradeAction:
        signals = []
        for comp, factors in self.cfg.items():
            for factor, threshold in factors.items():
                operator = self.get_trade_func_by_factor(factor)
                signals.append(operator(ohclv[comp], threshold))
        return sum(signals, start=TradeAction.HOLD)

# ohclv = pd.read_csv('HK.09866.csv', index_col='date', parse_dates=True)
# turtle = StrategyTurtle()
# logger.info(ohclv.loc['2022-04-04'])
# logger.info(turtle.execute_trade(ohclv.loc['2022-04-04']))