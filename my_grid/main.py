# -*- coding:utf-8 -*-
import datetime

import numpy as np

from my_grid import backtest, my_strategy
from my_grid.config import BackTestConfig

if __name__ == "__main__":
    grid_params = {
        "top": 20,
        "bottom": 10,
        "step_percent": 0.08,
    }
    opt_grid_params = {
        "top": range(15, 26),
        "bottom": range(8, 14),
        "step_percent": np.arange(start=0.05, stop=0.15, step=0.01),
    }
    backtest_config = BackTestConfig(strategy=my_strategy.GridStrategy,
                                     start=datetime.datetime(2024, 1, 1),
                                     end=datetime.datetime(2025, 1, 1),
                                     code=["300363"],
                                     name=["博腾股份"],
                                     file_name=[r"stock/sz.300363_60_2023-01-01.csv"],
                                     cash=20000,
                                     draw_plot=False
                                     )
    run_opt = False
    if run_opt:
        backtest_config.grid_params = opt_grid_params
        backtest = backtest.BackTest(backtest_config)
        result = backtest.run_opt()
    else:
        backtest_config.grid_params = grid_params
        backtest = backtest.BackTest(backtest_config)
        result = backtest.run()
    print(result)
