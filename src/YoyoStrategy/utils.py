import numpy as np
import itertools
from datetime import datetime, timedelta

def after_n_days(cur_date: str, period: int):
    """get the date after current date n days

    Args:
        cur_date (str): current date, a str in a form of %Y-%m-%d
        period (int): number of days after
    """
    cur_date = datetime(*[int(x) for x in cur_date.split('-')]).date()
    return cur_date + timedelta(days=period)

def dict_product(stride: float, params: dict):
    """generate all possible combinations of parameters

    Args:
        stride (float): stride of the range
        params (dict): a dict that contains ranges of the parameters
    """
    for key, val in params.items():
        if type(val) is float:
            params[key] = [val]
        elif len(val) == 1:
            continue
        elif val[0] == val[1]:
            params[key] = [val[0]]

    param_values = {key: np.arange(*values, step=stride) for key, values in params.items()}
    combinations = list(itertools.product(*param_values.values()))

    param_combinations = []
    for combination in combinations:
        param_combinations.append({key: value for key, value in zip(params.keys(), combination)})
    return param_combinations
