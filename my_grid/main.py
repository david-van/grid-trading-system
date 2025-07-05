# -*- coding:utf-8 -*-
import datetime

from my_grid import backtest, my_strategy
from my_grid.config import BackTestConfig

if __name__ == "__main__":
    start = "2024-01-01"
    end = "2025-05-05"
    name = ["博腾股份"]
    code = ["300363"]
    file_name = 'sz.300363_60_2023-01-01.csv'
    backtest_config = BackTestConfig(strategy=my_strategy.GridStrategy,
                                     start=datetime.datetime(2024, 1, 1),
                                     end=datetime.datetime(2025, 5, 1),
                                     code=["300363"],
                                     name=["博腾股份"],
                                     file_name=["sz.300363_60_2023-01-01.csv"],
                                     cash=20000,
                                     draw_plot=True
                                     )
    backtest = backtest.BackTest(backtest_config)
    result = backtest.run()
    print(result)
