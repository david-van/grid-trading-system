#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2025/7/2 22:46
# @Author  : david_van
# @Desc    :
# coding:utf-8
# 量化交易回测类


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
        self._cerebro.addstrategy(self.__config.strategy)

        self._raw_result = None
        self._backtest_summary = pd.Series()
        self._strategy_returns = pd.Series()
        self._benchmark_returns = pd.Series()
        self._benchFeed = None

        self._get_data_feeds()
        self._config_cerebro()

    # 执行回测
    def run(self):
        self._backtest_summary["期初账户总值"] = self.getValue()
        self._raw_result = self._cerebro.run()
        self.populate_summary()
        #  计算风险汇报
        self._risk_analyze()
        if self.__config.draw_plot:
            PerformanceVisualizer.draw_result(self._cerebro)
            PerformanceVisualizer.plot_performance(self._get_strategy_returns(self._raw_result))
        return self._backtest_summary

    # 获取账户总价值
    def getValue(self):
        return self._cerebro.broker.getvalue()

    # 获取策略及基准策略收益率的序列
    # def getReturns(self):
    #     return self._strategy_returns, self._benchmark_returns

    # 执行参数优化的回测
    # def optRun(self, *args, **kwargs):
    #     self._optStrategy(*args, **kwargs)
    #     results = self.__cerebro.run()
    #     if len(kwargs) == 1:
    #         testResults = self._optResult(results, **kwargs)
    #     elif len(kwargs) > 1:
    #         testResults = self._optResultMore(results, **kwargs)
    #     self._init()
    #     return testResults

    # 进行参数优化
    def _optStrategy(self, *args, **kwargs):
        self._cerebro = bt.Cerebro(maxcpus=1)
        self._cerebro.optstrategy(self.__config.strategy, *args, **kwargs)
        self._get_data_feeds()
        self._config_cerebro()

    # 设置cerebro
    def _config_cerebro(self):
        # 添加回撤观察器
        self._cerebro.addobserver(bt.observers.DrawDown)
        # 添加基准观察器
        self._cerebro.addobserver(bt.observers.Benchmark, data=self._benchFeed, timeframe=bt.TimeFrame.NoTimeFrame)
        # 设置手续费
        self._cerebro.broker.addcommissioninfo(StockCommission())

        # filler = bt.broker.fillers.FixedSize(size=200)
        # self.__cerebro.broker.set_filler(filler)
        # 设置收盘成交作弊模式
        # self.__cerebro.broker.set_coc(True)
        # 设置初始资金
        self._cerebro.broker.setcash(self.__config.cash)
        # 添加分析对象
        self._cerebro.addanalyzer(btay.SharpeRatio, _name="sharpe", riskfreerate=0.02, stddev_sample=True,
                                  annualize=True)
        self._cerebro.addanalyzer(btay.AnnualReturn, _name="AR")
        self._cerebro.addanalyzer(btay.DrawDown, _name="DD")
        self._cerebro.addanalyzer(btay.Returns, _name="RE")
        self._cerebro.addanalyzer(btay.TradeAnalyzer, _name="TA")
        self._cerebro.addanalyzer(btay.TimeReturn, _name="TR")
        self._cerebro.addanalyzer(btay.TimeReturn, _name="TR_Bench", data=self._benchFeed)
        self._cerebro.addanalyzer(btay.SQN, _name="SQN")
        # self.__cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='_TimeReturn')

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
            self._cerebro.adddata(dataFeed, name="benchMark")

    # 计算并保存回测结果指标
    def populate_summary(self):
        self._backtest_summary["期末账户总值"] = self.getValue()
        self._backtest_summary["账户总额"] = self.getValue()
        self._backtest_summary["总收益率"] = self._raw_result[0].analyzers.RE.get_analysis()["rtot"]
        self._backtest_summary["年化收益率"] = self._raw_result[0].analyzers.RE.get_analysis()["rnorm"]
        self._backtest_summary["年化收益率2"] = self._raw_result[0].analyzers.AR.get_analysis()
        # self.__backtestResult["交易成本"] = self.__cerebro.strats[0].getCommission()
        self._backtest_summary["夏普比率"] = self._raw_result[0].analyzers.sharpe.get_analysis()["sharperatio"]
        self._backtest_summary["最大回撤"] = self._raw_result[0].analyzers.DD.get_analysis().max.drawdown
        self._backtest_summary["最大回撤期间"] = self._raw_result[0].analyzers.DD.get_analysis().max.len
        self._backtest_summary["SQN"] = self._raw_result[0].analyzers.SQN.get_analysis()["sqn"]
        self._backtest_summary["策略评价(根据SQN)"] = IndicatorAnalyzer.judge_by_SQN(self._backtest_summary["SQN"])

        # 计算胜率信息
        self._calc_win_info(self._backtest_summary)

    # 计算胜率信息
    def _calc_win_info(self, result):
        trade_info = self._raw_result[0].analyzers.TA.get_analysis()
        total_trade_num = trade_info["total"]["total"]
        if total_trade_num > 1:
            win_num = trade_info["won"]["total"]
            lost_num = trade_info["lost"]["total"]
            result["交易次数"] = total_trade_num
            result["胜率"] = win_num / total_trade_num
            result["败率"] = lost_num / total_trade_num

    def _get_strategy_returns(self, result):
        return pd.Series(result[0].analyzers.TR.get_analysis())

    # 运行基准策略，获取基准收益值
    def _getBenchmarkReturns(self, result):
        return pd.Series(result[0].analyzers.TR_Bench.get_analysis())

    # 分析策略的风险指标
    def _risk_analyze(self) -> None:
        self._strategy_returns = self._get_strategy_returns(self._raw_result)
        self._benchmark_returns = self._getBenchmarkReturns(self._raw_result)
        risk = RiskAnalyzer(self._strategy_returns, self._benchmark_returns)
        result = risk.run()
        self._backtest_summary.update(result.to_dict())

    # 取得优化参数时的指标结果
    # def _getOptAnalysis(self, result):
    #     temp = dict()
    #     temp["总收益率"] = result[0].analyzers.RE.get_analysis()["rtot"]
    #     temp["年化收益率"] = result[0].analyzers.RE.get_analysis()["rnorm"]
    #     temp["夏普比率"] = result[0].analyzers.sharpe.get_analysis()["sharperatio"]
    #     temp["最大回撤"] = result[0].analyzers.DD.get_analysis().max.drawdown
    #     temp["最大回撤期间"] = result[0].analyzers.DD.get_analysis().max.len
    #     sqn = result[0].analyzers.SQN.get_analysis()["sqn"]
    #     temp["SQN"] = sqn
    #     temp["策略评价(根据SQN)"] = self._judgeBySQN(sqn)
    #     trade_info = self.__results[0].analyzers.TA.get_analysis()
    #     self._winInfo(trade_info, temp)
    #     return temp

    # 在优化多个参数时计算并保存回测结果
    # def _optResultMore(self, results, **kwargs):
    #     testResults = pd.DataFrame()
    #     i = 0
    #     for key in kwargs:
    #         for value in kwargs[key]:
    #             temp = self._getOptAnalysis(results[i])
    #             temp["参数名"] = key
    #             temp["参数值"] = value
    #             returns = self._timeReturns(results[i])
    #             benchReturns = self._getBenchmarkReturns(results[i])
    #             self._riskAnaly(returns, benchReturns, temp)
    #             testResults = testResults.append(temp, ignore_index=True)
    #         # testResults.set_index(["参数值"], inplace = True)
    #     return testResults

    # 在优化参数时计算并保存回测结果
    # def _optResult(self, results, **kwargs):
    #     testResults = pd.DataFrame()
    #     params = []
    #     for k, v in kwargs.items():
    #         for t in v:
    #             params.append(t)
    #     i = 0
    #     for result in results:
    #         temp = self._getOptAnalysis(result)
    #         temp["参数名"] = k
    #         temp["参数值"] = params[i]
    #         i += 1
    #         returns = self._timeReturns(result)
    #         benchReturns = self._getBenchmarkReturns(result)
    #         self._riskAnaly(returns, benchReturns, temp)
    #         testResults = testResults.append(temp, ignore_index=True)
    #     # testResults.set_index(["参数值"], inplace = True)
    #     return testResults
