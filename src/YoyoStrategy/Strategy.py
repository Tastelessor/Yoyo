import os
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import List, Callable, Any
import pandas as pd
import json
from YoyoLogger import logger
from YoyoStrategy import CWD

FuncType = Callable[..., Any]

# Define an enumeration for trade actions
class TradeAction(Enum):
    BUY = 1
    SELL = -1
    HOLD = 0

    def __add__(self, other):
        if other is None:
            return self.value
        
        if isinstance(other, TradeAction):
            total = self.value + other.value
            if total > 0:
                return TradeAction.BUY
            elif total < 0:
                return TradeAction.SELL
            else:
                return TradeAction.HOLD
        raise NotImplementedError

class Strategy(ABC):
    def __init__(self) -> None:
        self.day = 0
        self.cfg = dict()

    @abstractmethod
    def execute_trade(self, data):
        pass

    def load_config(self, class_name=None, cfg='{CWD}/strategy_cfg.json'):
        if type(cfg) is str:
            logger.info(f'Loading strategy config from {cfg}')
            with open(cfg, 'r') as f:
                obj = json.load(f)
                if class_name is not None and class_name in obj:
                    self.cfg = obj.get(class_name)
                else:
                    self.cfg = obj
        elif type(cfg) is dict:
            logger.info(f'Loading strategy config from dict')
            self.cfg = cfg
        
    def process_factors(self, func_list: List[FuncType], args_list: List[list[Any]]) -> TradeAction:
        # Process the factors to generate a trading signal
        signals = []
        for func in func_list:
            signals.append(func(*args_list))
        return sum(signals, start=TradeAction.HOLD)