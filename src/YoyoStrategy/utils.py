import numpy as np
import itertools
from datetime import datetime, timedelta
from YoyoLogger import logger

def after_n_days(cur_date: str, period: int):
    """get the date after current date n days

    Args:
        cur_date (str): current date, a str in a form of %Y-%m-%d
        period (int): number of days after
    """
    cur_date = datetime(*[int(x) for x in str(cur_date).split('-')]).date()
    return cur_date + timedelta(days=period)

def params_product(stride: float, params: dict):
    """generate all possible combinations of parameters

    Args:
        stride (float): stride of the range
        params (dict): a dict that contains ranges of the parameters
    """
    logger.debug(f"Generating combinations for {params}")
    for key, val in params.items():
        if type(val) is float:
            params[key] = [val]
        elif len(val) == 1:
            continue
        elif val[0] == val[1]:
            params[key] = [val[0]]

    param_values = {key: np.arange(*values, step=stride) if len(values) == 2 else values for key, values in params.items()}
    combinations = list(itertools.product(*param_values.values()))

    param_combinations = []
    for combination in combinations:
        param_combinations.append({key: value for key, value in zip(params.keys(), combination)})

    logger.debug(f"Generated {len(param_combinations)} combinations")
    logger.debug(f"First combination: {param_combinations[0]}")
    return param_combinations

def strategy_product(strategy_comb: dict) -> list:
    """generate all possible combinations of strategies

    Args:
        strategy_comb (dict): strategy combinations
    """
    # generate all possible combinations of strategies
    combs = []
    name_list = {}
    for strategy, attributes in strategy_comb.items():
        name_list[strategy] =  [*attributes.keys()]
        combs.append(list(itertools.product(*attributes.values())))
    comb_list = list(itertools.product(*combs))

    res_list = []
    attributes = list(name_list.values())
    # composite combinations into a list of dict
    for comb in comb_list:
        attr_comb = {}
        # assign attribute name to each combination
        for i, attribute in enumerate(attributes):
            for j, attribute_name in enumerate(attribute):
                attr_comb[attribute_name] = comb[i][j]
        # generate a dict for each combination
        res = {}
        for strategy, attrs in name_list.items():
            res[strategy] = {}
            for attr in attrs:
                res[strategy][attr] = attr_comb[attr]
        res_list.append(res)
    
    logger.debug(f"Generated {len(res_list)} combinations")
    logger.debug(f"First combination: {res_list[0]}")
    return res_list
    