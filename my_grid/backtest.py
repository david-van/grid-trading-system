#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2025/7/2 22:46
# @Author  : david_van
# @Desc    :
# coding:utf-8
# 量化交易回测类
import datetime

import backtrader as bt
import backtrader.analyzers as btay
import pandas as pd

from my_grid.analyzer import RiskAnalyzer, IndicatorAnalyzer
from my_grid.commission_scheme import StockCommission
from my_grid.config import BackTestConfig
from my_grid.read_data import get_data_by_date
from my_grid.visualization import PerformanceVisualizer


# 回测类
class BackTest:
    def __init__(self, config: BackTestConfig):
        self.__config = config
        self._cerebro = bt.Cerebro()

        self._raw_result = None
        self._backtest_summary = pd.Series()
        self._strategy_returns = pd.Series()
        self._benchmark_returns = pd.Series()
        self._benchFeed = None

        self._get_data_feeds()
        self._config_cerebro()

    # 执行回测
    def run(self):
        self._backtest_summary["期初账户总值"] = self.get_value()
        self._cerebro.addstrategy(self.__config.strategy, **self.__config.grid_params)
        self._raw_result = self._cerebro.run(stdstats=False)
        self.populate_summary()
        #  计算风险汇报
        self._risk_analyze()
        if self.__config.draw_plot:
            PerformanceVisualizer.draw_result(self._cerebro)
            # PerformanceVisualizer.plot_performance(self._get_strategy_returns(self._raw_result))
            # pyfoliozer = self._raw_result[0].analyzers.getbyname('PyFolio')
            # PerformanceVisualizer.show_by_pyfolio(pyfoliozer)

        return self._backtest_summary

    def run_opt(self):
        self._backtest_summary["期初账户总值"] = self.get_value()
        # 遍历参数
        self._cerebro.optstrategy(
            self.__config.strategy,
            **self.__config.grid_params)
        results = self._cerebro.run(stdstats=False, optreturn=False)
        records = []
        print(f'results length is {len(results)}')
        for run in results:
            strat = run[0]
            p = strat.params
            # 数据重置
            self._raw_result = run
            self._backtest_summary = pd.Series()
            self._strategy_returns = pd.Series()
            self._benchmark_returns = pd.Series()
            # self._benchFeed = None
            self.populate_summary()
            map_summary = {
                'top': p.top, 'bottom': p.bottom,
                'step_percent': p.step_percent
            }
            #  计算风险汇报
            self._risk_analyze()
            # if self.__config.draw_plot:
            # PerformanceVisualizer.draw_result(self._cerebro)
            # PerformanceVisualizer.plot_performance(self._get_strategy_returns(self._raw_result))
            # pyfoliozer = self._raw_result[0].analyzers.getbyname('PyFolio')
            # PerformanceVisualizer.show_by_pyfolio(pyfoliozer)
            map_summary.update(self._backtest_summary.to_dict())
            records.append(map_summary)
        if self.__config.draw_plot:
            PerformanceVisualizer.draw_result(self._cerebro)
        # 将 records 转换为 DataFrame 并保存为 CSV
        df_records = pd.DataFrame(records)
        current_date = datetime.datetime.now().date().isoformat()
        df_records.to_csv(f'grid_opt_results_{current_date}.csv', index=False, encoding='utf-8-sig')

        return df_records

    def _config_cerebro(self):
        # cerebro = bt.Cerebro() #默认参数: stdstats=True
        # cerebro.addobserver(bt.observers.Broker)
        # cerebro.addobserver(bt.observers.Trades)
        # cerebro.addobserver(bt.observers.BuySell)
        # | Observer    | 功能             | 图表表现        |
        # | ----------- | -------------- | ----------- |
        # | **Broker**  | 追踪现金与账户净值      | 折线图/子图      |
        # | **Trades**  | 记录每笔交易的盈亏      | 盈亏标注、子图或图点  |
        # | **BuySell** | 标记所有成交的买入/卖出时点 | 箭头/点状显示在主图上 |

        self._cerebro.addobserver(bt.observers.Broker)
        self._cerebro.addobserver(bt.observers.BuySell)
        # 添加回撤观察器
        self._cerebro.addobserver(bt.observers.DrawDown)
        # self._cerebro.addobserver(bt.observers.Value)
        # 移除trade
        # 添加基准观察器
        # self._cerebro.addobserver(bt.observers.Benchmark, data=self._benchFeed, timeframe=bt.TimeFrame.NoTimeFrame)
        # 设置手续费
        self._cerebro.broker.addcommissioninfo(StockCommission())

        # filler = bt.broker.fillers.FixedSize(size=200)
        # self.__cerebro.broker.set_filler(filler)
        # 设置收盘成交作弊模式
        # self.__cerebro.broker.set_coc(True)
        # 设置初始资金
        self._cerebro.broker.setcash(self.__config.cash)
        # 添加分析对象
        self._cerebro.addanalyzer(btay.SharpeRatio, _name="SharpeRatio", riskfreerate=0.02, stddev_sample=False,
                                  annualize=True)
        self._cerebro.addanalyzer(btay.AnnualReturn, _name="AnnualReturn")
        self._cerebro.addanalyzer(btay.DrawDown, _name="DrawDown")
        self._cerebro.addanalyzer(btay.Returns, _name="Returns")
        self._cerebro.addanalyzer(btay.TradeAnalyzer, _name="TradeAnalyzer")
        self._cerebro.addanalyzer(btay.TimeReturn, _name="TimeReturn")
        self._cerebro.addanalyzer(btay.TimeReturn, _name="TimeReturn_Bench", data=self._benchFeed)
        self._cerebro.addanalyzer(btay.SQN, _name="SQN")
        # self.__cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='_TimeReturn')
        self._cerebro.addanalyzer(bt.analyzers.PyFolio, _name='PyFolio')

    def get_value(self):
        return self._cerebro.broker.get_value()

    # 建立数据源
    def _get_data_feeds(self):
        # 建立回测数据源
        for i in range(len(self.__config.code)):
            dataFeed = get_data_by_date(file_name=self.__config.file_name[i],
                                        start_time=self.__config.start,
                                        end_time=self.__config.end)
            dataFeed = bt.feeds.PandasData(dataname=dataFeed, name=self.__config.name[i])
            self._cerebro.adddata(dataFeed, name=self.__config.name[i])
            #  todo benchMark 待处理
            # self._cerebro.adddata(dataFeed, name="benchMark")

    # 计算并保存回测结果指标
    def populate_summary(self):
        self._backtest_summary["期末账户总值"] = self.get_value()
        self._backtest_summary["账户总额"] = self.get_value()
        self._backtest_summary["总收益率"] = self._raw_result[0].analyzers.Returns.get_analysis()["rtot"]
        self._backtest_summary["年化收益率"] = self._raw_result[0].analyzers.Returns.get_analysis()["rnorm"]
        self._backtest_summary["每年年化收益率"] = self._raw_result[0].analyzers.AnnualReturn.get_analysis()
        # self.__backtestResult["交易成本"] = self.__cerebro.strats[0].getCommission()
        self._backtest_summary["夏普比率"] = self._raw_result[0].analyzers.SharpeRatio.get_analysis()["sharperatio"]
        self._backtest_summary["最大回撤"] = self._raw_result[0].analyzers.DrawDown.get_analysis().max.drawdown
        # 当前采用的是小时数据，所以除以4
        self._backtest_summary["最大回撤期间"] = self._raw_result[0].analyzers.DrawDown.get_analysis().max.len // 4
        self._backtest_summary["SQN"] = self._raw_result[0].analyzers.SQN.get_analysis()["sqn"]
        self._backtest_summary["策略评价(根据SQN)"] = IndicatorAnalyzer.judge_by_SQN(self._backtest_summary["SQN"])

        # 计算胜率信息
        self._calc_win_info(self._backtest_summary)

    # 计算胜率信息
    def _calc_win_info(self, result):
        trade_info = self._raw_result[0].analyzers.TradeAnalyzer.get_analysis()
        total_trade_num = trade_info["total"]["total"]
        if total_trade_num > 1:
            win_num = trade_info["won"]["total"]
            lost_num = trade_info["lost"]["total"]
            result["交易次数"] = total_trade_num
            result["胜率"] = win_num / total_trade_num
            result["败率"] = lost_num / total_trade_num

    def _get_strategy_returns(self, result):
        return pd.Series(result[0].analyzers.TimeReturn.get_analysis())

    # 运行基准策略，获取基准收益值
    def _get_benchmark_returns(self, result):
        return pd.Series(result[0].analyzers.TimeReturn_Bench.get_analysis())

    # 分析策略的风险指标
    def _risk_analyze(self) -> None:
        self._strategy_returns = self._get_strategy_returns(self._raw_result)
        self._benchmark_returns = self._get_benchmark_returns(self._raw_result)
        risk = RiskAnalyzer(self._strategy_returns, self._benchmark_returns)
        result = risk.run()
        self._backtest_summary = pd.concat([self._backtest_summary, result])
