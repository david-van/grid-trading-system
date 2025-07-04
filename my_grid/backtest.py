#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2025/7/2 22:46
# @Author  : david_van
# @Desc    :
# coding:utf-8
# 量化交易回测类


import datetime
import os

import backtrader as bt
import backtrader.analyzers as btay
import empyrical as ey
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyfolio as pf
from backtrader.utils.py3 import map

class MyStockCommissionScheme(bt.CommInfoBase):
    '''
    1.佣金按照百分比。    2.每一笔交易有一个最低值，比如5块，当然有些券商可能会免5.
    3.卖出股票还需要收印花税。    4.可能有的平台还需要收平台费。    '''
    params = (
        ('stampduty', 0.0005),  # 印花税率
        ('commission', 0.0005),  # 佣金率
        ('stocklike', True),  # 股票类资产，不考虑保证金
        ('commtype', bt.CommInfoBase.COMM_PERC),  # 按百分比
        ('minCommission', 5),  # 最小佣金
        ('platFee', 0),  # 平台费用
    )

    def _getcommission(self, size, price, pseudoexec):
        '''
        size>0，买入操作。        size<0，卖出操作。        '''
        if size > 0:  # 买入，不考虑印花税，需要考虑最低收费
            return max(size * price * self.p.commission, self.p.minCommission) + self.p.platFee
        elif size < 0:  # 卖出，考虑印花税。
            return max(abs(size) * price * self.p.commission, self.p.minCommission) + abs(
                size) * price * self.p.stampduty + self.p.platFee
        else:
            return 0  # 防止特殊情况下size为0.


# 回测类
class BackTest:
    def __init__(self, strategy, start, end, code, name, cash=0.01, commission=0.0003, benchmarkCode="510300",
                 bDraw=True):
        self.__cerebro = None
        self.__strategy = strategy
        self.__start = start
        self.__end = end
        self.__code = code
        self.__name = name
        self.__result = None
        self.__commission = commission
        self.__initcash = cash
        self.__backtestResult = pd.Series()
        self.__returns = pd.Series()
        self.__benchmarkCode = benchmarkCode
        self.__benchReturns = pd.Series()
        self.__benchFeed = None
        self.__bDraw = bDraw
        self.__start_date = None
        self.__end_date = None
        self._init()

    # 执行回测
    def run(self):
        self.__backtestResult["期初账户总值"] = self.getValue()
        self.__results = self.__cerebro.run()
        self.__backtestResult["期末账户总值"] = self.getValue()
        self._Result()
        if self.__bDraw == True:
            self._drawResult()
        self.__returns = self._timeReturns(self.__results)
        self.show_1()
        self.__benchReturns = self._getBenchmarkReturns(self.__results)
        self._riskAnaly(self.__returns, self.__benchReturns, self.__backtestResult)
        return self.getResult()

    # 获取账户总价值
    def getValue(self):
        return self.__cerebro.broker.getvalue()

    # 获取回测指标
    def getResult(self):
        return self.__backtestResult

    # 获取策略及基准策略收益率的序列
    def getReturns(self):
        return self.__returns, self.__benchReturns

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

    # 输出回测结果
    def output(self):
        print("夏普比例:", self.__results[0].analyzers.sharpe.get_analysis()["sharperatio"])
        print("年化收益率:", self.__results[0].analyzers.AR.get_analysis())
        print("最大回撤:%.2f，最大回撤周期%d" % (self.__results[0].analyzers.DD.get_analysis().max.drawdown,
                                                self.__results[0].analyzers.DD.get_analysis().max.len))
        print("总收益率:%.2f" % (self.__results[0].analyzers.RE.get_analysis()["rtot"]))
        # self.__results[0].analyzers.TA.pprint()

    # 进行参数优化
    def _optStrategy(self, *args, **kwargs):
        self.__cerebro = bt.Cerebro(maxcpus=1)
        self.__cerebro.optstrategy(self.__strategy, *args, **kwargs)
        self._createDataFeeds()
        self._settingCerebro()

    # 真正进行初始化的地方
    def _init(self):
        self.__cerebro = bt.Cerebro()
        self.__cerebro.addstrategy(self.__strategy)
        self._createDataFeeds()
        self._settingCerebro()

    # 设置cerebro
    def _settingCerebro(self):
        # 添加回撤观察器
        self.__cerebro.addobserver(bt.observers.DrawDown)
        # 添加基准观察器
        self.__cerebro.addobserver(bt.observers.Benchmark, data=self.__benchFeed, timeframe=bt.TimeFrame.NoTimeFrame)
        # 设置手续费
        # self.__cerebro.broker.setcommission(commission=self.__commission)
        self.__cerebro.broker.addcommissioninfo(MyStockCommissionScheme())

        filler = bt.broker.fillers.FixedSize(size=200)
        self.__cerebro.broker.set_filler(filler)
        # 设置收盘成交作弊模式
        self.__cerebro.broker.set_coc(True)
        # 设置初始资金
        self.__cerebro.broker.setcash(self.__initcash)
        # 添加分析对象
        self.__cerebro.addanalyzer(btay.SharpeRatio, _name="sharpe", riskfreerate=0.02, stddev_sample=True,
                                   annualize=True)
        self.__cerebro.addanalyzer(btay.AnnualReturn, _name="AR")
        self.__cerebro.addanalyzer(btay.DrawDown, _name="DD")
        self.__cerebro.addanalyzer(btay.Returns, _name="RE")
        self.__cerebro.addanalyzer(btay.TradeAnalyzer, _name="TA")
        self.__cerebro.addanalyzer(btay.TimeReturn, _name="TR")
        self.__cerebro.addanalyzer(btay.TimeReturn, _name="TR_Bench", data=self.__benchFeed)
        self.__cerebro.addanalyzer(btay.SQN, _name="SQN")
        # self.__cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='_TimeReturn')

    # 建立数据源
    def _createDataFeeds(self):
        # 建立回测数据源
        for i in range(len(self.__code)):
            dataFeed = self._createDataFeedsProcess(self.__code[i], self.__name[i])
            self.__cerebro.adddata(dataFeed, name=self.__name[i])
        self.__benchFeed = self._createDataFeedsProcess(self.__benchmarkCode, "benchMark")
        self.__cerebro.adddata(self.__benchFeed, name="benchMark")

    # 建立数据源的具体过程
    def _createDataFeedsProcess(self, code, name):
        df_data = self._getData(code)
        start_date = list(map(int, self.__start.split("-")))
        end_date = list(map(int, self.__end.split("-")))
        self.__start_date = datetime.datetime(start_date[0], start_date[1], start_date[2])
        self.__end_date = datetime.datetime(end_date[0], end_date[1], end_date[2])
        dataFeed = bt.feeds.PandasData(dataname=df_data, name=name,
                                       fromdate=datetime.datetime(start_date[0], start_date[1], start_date[2]),
                                       todate=datetime.datetime(end_date[0], end_date[1], end_date[2]))
        return dataFeed

    # 计算胜率信息
    def _winInfo(self, trade_info, result):
        total_trade_num = trade_info["total"]["total"]
        if total_trade_num > 1:
            win_num = trade_info["won"]["total"]
            lost_num = trade_info["lost"]["total"]
            result["交易次数"] = total_trade_num
            result["胜率"] = win_num / total_trade_num
            result["败率"] = lost_num / total_trade_num

    # 根据SQN值对策略做出评估
    # 按照backtrader文档写的
    def _judgeBySQN(self, sqn):
        result = None
        if sqn >= 1.6 and sqn <= 1.9:
            result = "低于平均"
        elif sqn > 1.9 and sqn <= 2.4:
            result = "平均水平"
        elif sqn > 2.4 and sqn <= 2.9:
            result = "良好"
        elif sqn > 2.9 and sqn <= 5.0:
            result = "优秀"
        elif sqn > 5.0 and sqn <= 6.9:
            result = "卓越"
        elif sqn > 6.9:
            result = "大神?"
        else:
            result = "很差"
        self.__backtestResult["策略评价(根据SQN)"] = result
        return result

    # 计算并保存回测结果指标
    def _Result(self):
        self.__backtestResult["账户总额"] = self.getValue()
        self.__backtestResult["总收益率"] = self.__results[0].analyzers.RE.get_analysis()["rtot"]
        self.__backtestResult["年化收益率"] = self.__results[0].analyzers.RE.get_analysis()["rnorm"]
        # self.__backtestResult["交易成本"] = self.__cerebro.strats[0].getCommission()
        self.__backtestResult["夏普比率"] = self.__results[0].analyzers.sharpe.get_analysis()["sharperatio"]
        self.__backtestResult["最大回撤"] = self.__results[0].analyzers.DD.get_analysis().max.drawdown
        self.__backtestResult["最大回撤期间"] = self.__results[0].analyzers.DD.get_analysis().max.len
        self.__backtestResult["SQN"] = self.__results[0].analyzers.SQN.get_analysis()["sqn"]
        self._judgeBySQN(self.__backtestResult["SQN"])

        # 计算胜率信息
        trade_info = self.__results[0].analyzers.TA.get_analysis()
        self._winInfo(trade_info, self.__backtestResult)

    def show_1(self):
        # 按年统计收益指标
        pnl = self.__returns
        # 计算累计收益
        cumulative = (pnl + 1).cumprod()
        # 计算回撤序列
        max_return = cumulative.cummax()
        drawdown = (cumulative - max_return) / max_return

        # 计算收益评价指标
        perf_stats_year = (pnl).groupby(pnl.index.to_period('y')).apply(
            lambda data: pf.timeseries.perf_stats(data)).unstack()
        # 统计所有时间段的收益指标
        perf_stats_all = pf.timeseries.perf_stats((pnl)).to_frame(name='all')
        perf_stats = pd.concat([perf_stats_year, perf_stats_all.T], axis=0)
        perf_stats_ = round(perf_stats, 4).reset_index()

        # 绘制图形

        plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
        import matplotlib.ticker as ticker  # 导入设置坐标轴的模块
        # plt.style.use('seaborn')
        plt.style.use('dark_background')

        fig, (ax0, ax1) = plt.subplots(2, 1, gridspec_kw={'height_ratios': [1.5, 4]}, figsize=(20, 8))
        cols_names = ['date', 'Annual\nreturn', 'Cumulative\nreturns', 'Annual\nvolatility',
                      'Sharpe\nratio', 'Calmar\nratio', 'Stability', 'Max\ndrawdown',
                      'Omega\nratio', 'Sortino\nratio', 'Skew', 'Kurtosis', 'Tail\nratio',
                      'Daily value\nat risk']

        # 绘制表格
        ax0.set_axis_off()  # 除去坐标轴
        table = ax0.table(cellText=perf_stats_.values,
                          bbox=(0, 0, 1, 1),  # 设置表格位置， (x0, y0, width, height)
                          rowLoc='right',  # 行标题居中
                          cellLoc='right',
                          colLabels=cols_names,  # 设置列标题
                          colLoc='right',  # 列标题居中
                          edges='open'  # 不显示表格边框
                          )
        table.set_fontsize(13)

        # 绘制累计收益曲线
        ax2 = ax1.twinx()
        ax1.yaxis.set_ticks_position('right')  # 将回撤曲线的 y 轴移至右侧
        ax2.yaxis.set_ticks_position('left')  # 将累计收益曲线的 y 轴移至左侧
        # 绘制回撤曲线
        drawdown.plot.area(ax=ax1, label='drawdown (right)', rot=0, alpha=0.3, fontsize=13, grid=False)
        # 绘制累计收益曲线
        (cumulative).plot(ax=ax2, color='#F1C40F', lw=3.0, label='cumret (left)', rot=0, fontsize=13, grid=False)
        # 不然 x 轴留有空白
        ax2.set_xbound(lower=cumulative.index.min(), upper=cumulative.index.max())
        # 主轴定位器：每 5 个月显示一个日期：根据具体天数来做排版
        ax2.xaxis.set_major_locator(ticker.MultipleLocator(100))
        # 同时绘制双轴的图例
        h1, l1 = ax1.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        plt.legend(h1 + h2, l1 + l2, fontsize=12, loc='upper left', ncol=1)

        fig.tight_layout()  # 规整排版
        plt.show()

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

    # 计算收益率序列
    def _timeReturns(self, result):
        return pd.Series(result[0].analyzers.TR.get_analysis())

    # 运行基准策略，获取基准收益值
    def _getBenchmarkReturns(self, result):
        return pd.Series(result[0].analyzers.TR_Bench.get_analysis())

    # 分析策略的风险指标
    def _riskAnaly(self, returns, benchReturns, results):
        risk = riskAnalyzer(returns, benchReturns)
        result = risk.run()
        results["阿尔法"] = result["阿尔法"]
        results["贝塔"] = result["贝塔"]
        results["信息比例"] = result["信息比例"]
        results["策略波动率"] = result["策略波动率"]
        results["欧米伽"] = result["欧米伽"]
        # self.__backtestResult["夏普值"] = result["夏普值"]
        results["sortino"] = result["sortino"]
        results["calmar"] = result["calmar"]

    # 回测结果绘图
    def _drawResult(self):
        self.__cerebro.plot(numfigs=1)
        figname = type(self).__name__ + ".png"
        plt.savefig(figname)

    def _getData(self, code):
        _data_root = r'D:\code\pycharm\test\grid-trading-system\my_grid'
        file_name = 'sz.300363_60_2023-01-01.csv'
        data_path = os.path.join(_data_root, file_name)
        print(f'data_path is {data_path}')

        df = pd.read_csv(data_path).rename(columns=lambda x: x.strip())
        df['openinterest'] = 0  # 添加一列数据
        # data = df.loc[:, ['open', 'high', 'low', 'close', 'vol', 'openinterest', 'trade_date']]  # 选择需要的数据
        # df = df.loc[2:]
        data = df.loc[:, ['time', 'open', 'high', 'low', 'close', 'amount', 'openinterest']]  # 选择需要的数据
        data.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume', 'openinterest']  # 修改列名
        data = data.set_index(
            pd.to_datetime(
                data['datetime'],
                format='%Y%m%d%H%M%S%f'
                , errors='coerce')).sort_index()  # 把datetime列改为时间格式并排序
        # 这个数据是整理过的，实际操作中可能会有一下缺失数据，所以需要做一下填充。
        # data.loc[:, ['volume', 'openinterest']] = data.loc[:, ['volume', 'openinterest']].ffill(0)
        # data.loc[:, ['open', 'high', 'low', 'close']] = data.loc[:, ['open', 'high', 'low', 'close']].ffill(
        #     method='pad')
        # data.loc[:, ['volume']] = data.loc[:, ['volume']] * 1000
        # filename = code + ".csv"
        # path = "./data/"
        # # 如果数据目录不存在，创建目录
        # if not os.path.exists(path):
        #     os.makedirs(path)
        # # 已有数据文件，直接读取数据
        # if os.path.exists(path + filename):
        #     df = pd.read_csv(path + filename)
        # else:  # 没有数据文件，用tushare下载
        #     df = ts.get_k_data(code, autype="qfq", start=self.__start, end=self.__end)
        #     df.to_csv(path + filename)
        # df.index = pd.to_datetime(df.date)
        # df['openinterest'] = 0
        # df = df[['open', 'high', 'low', 'close', 'volume', 'openinterest']]
        return data


# 用empyrical库计算风险指标
class riskAnalyzer:
    def __init__(self, returns, benchReturns, riskFreeRate=0.02):
        self.__returns = returns
        self.__benchReturns = benchReturns
        self.__risk_free = riskFreeRate
        self.__alpha = 0.0
        self.__beta = 0.0
        self.__info = 0.0
        self.__vola = 0.0
        self.__omega = 0.0
        self.__sharpe = 0.0
        self.__sortino = 0.0
        self.__calmar = 0.0

    def run(self):
        # 计算各指标
        self._alpha_beta()
        self._info()
        self._vola()
        self._omega()
        self._sharpe()
        self._sortino()
        self._calmar()
        result = pd.Series(dtype="float64")
        result["阿尔法"] = self.__alpha
        result["贝塔"] = self.__beta
        result["信息比例"] = self.__info
        result["策略波动率"] = self.__vola
        result["欧米伽"] = self.__omega
        result["夏普值"] = self.__sharpe
        result["sortino"] = self.__sortino
        result["calmar"] = self.__calmar
        return result

    def _alpha_beta(self):
        self.__alpha, self.__beta = ey.alpha_beta(returns=self.__returns, factor_returns=self.__benchReturns,
                                                  risk_free=self.__risk_free, annualization=1)

    def _info(self):
        self.__info = ey.excess_sharpe(returns=self.__returns, factor_returns=self.__benchReturns)

    def _vola(self):
        self.__vola = ey.annual_volatility(self.__returns, period='daily')

    def _omega(self):
        self.__omega = ey.omega_ratio(returns=self.__returns, risk_free=self.__risk_free)

    def _sharpe(self):
        self.__sharpe = ey.sharpe_ratio(returns=self.__returns, annualization=1)

    def _sortino(self):
        self.__sortino = ey.sortino_ratio(returns=self.__returns)

    def _calmar(self):
        self.__calmar = ey.calmar_ratio(returns=self.__returns)


# 测试函数
# def test():
#     # 构造测试数据
#     returns = pd.Series(
#         index=pd.date_range("2017-03-10", "2017-03-19"),
#         data=(-0.012143, 0.045350, 0.030957, 0.004902, 0.002341, -0.02103, 0.00148, 0.004820, -0.00023, 0.01201))
#     print(returns)
#     benchmark_returns = pd.Series(
#         index=pd.date_range("2017-03-10", "2017-03-19"),
#         data=(-0.031940, 0.025350, -0.020957, -0.000902, 0.007341, -0.01103, 0.00248, 0.008820, -0.00123, 0.01091))
#     print(benchmark_returns)
#     # 计算累积收益率
#     creturns = ey.cum_returns(returns)
#     print("累积收益率\n", creturns)
#     risk = riskAnalyzer(returns, benchmark_returns, riskFreeRate=0.01)
#     results = risk.run()
#     print(results)
#     # 直接调用empyrical试试
#     alpha = ey.alpha(returns=returns, factor_returns=benchmark_returns, risk_free=0.01)
#     calmar = ey.calmar_ratio(returns)
#     print(alpha, calmar)
#     # 自己计算阿尔法值
#     annual_return = ey.annual_return(returns)
#     annual_bench = ey.annual_return(benchmark_returns)
#     print(annual_return, annual_bench)
#     alpha2 = (annual_return - 0.01) - results["贝塔"] * (annual_bench - 0.01)
#     print(alpha2)
#
#     # 自己计算阿尔法贝塔
#     def get_return(code, startdate, endate):
#         df = ts.get_k_data(code, ktype="D", autype="qfq", start=startdate, end=endate)
#         p1 = np.array(df.close[1:])
#         p0 = np.array(df.close[:-1])
#         logret = np.log(p1 / p0)
#         rate = pd.DataFrame()
#         rate[code] = logret
#         rate.index = df["date"][1:]
#         return rate
#
#     def alpha_beta(code, startdate, endate):
#         mkt_ret = get_return("sh", startdate, endate)
#         stock_ret = get_return(code, startdate, endate)
#         df = pd.merge(mkt_ret, stock_ret, left_index=True, right_index=True)
#         x = df.iloc[:, 0]
#         y = df.iloc[:, 1]
#         beta, alpha, r_value, p_value, std_err = stats.linregress(x, y)
#         return (alpha, beta)
#
#     def stocks_alpha_beta(stocks, startdate, endate):
#         df = pd.DataFrame()
#         alpha = []
#         beta = []
#         for code in stocks.values():
#             a, b = alpha_beta(code, startdate, endate)
#             alpha.append(float("%.4f" % a))
#             beta.append(float("%.4f" % b))
#         df["alpha"] = alpha
#         df["beta"] = beta
#         df.index = stocks.keys()
#         return df
#
#     startdate = "2017-01-01"
#     endate = "2018-11-09"
#     stocks = {'中国平安': '601318', '格力电器': '000651', '招商银行': '600036', '恒生电子': '600570',
#               '中信证券': '600030',
#               '贵州茅台': '600519'}
#     results = stocks_alpha_beta(stocks, startdate, endate)
#     print("自己计算结果")
#     print(results)
#
#     # 用empyrical计算
#     def stocks_alpha_beta2(stocks, startdate, endate):
#         df = pd.DataFrame()
#         alpha = []
#         beta = []
#         for code in stocks.values():
#             a, b = empyrical_alpha_beta(code, startdate, endate)
#             alpha.append(float("%.4f" % a))
#             beta.append(float("%.4f" % b))
#         df["alpha"] = alpha
#         df["beta"] = beta
#         df.index = stocks.keys()
#         return df
#
#     def empyrical_alpha_beta(code, startdate, endate):
#         mkt_ret = get_return("sh", startdate, endate)
#         stock_ret = get_return(code, startdate, endate)
#         alpha, beta = ey.alpha_beta(returns=stock_ret, factor_returns=mkt_ret, annualization=1)
#         return (alpha, beta)
#
#     results2 = stocks_alpha_beta2(stocks, startdate, endate)
#     print("empyrical计算结果")
#     print(results2)
#     print(results2["alpha"] / results["alpha"])


# 测试夏普值的计算
def testSharpe():
    # 读取数据
    stock_data = pd.read_csv("stock_data.csv", parse_dates=["Date"], index_col=["Date"]).dropna()
    benchmark_data = pd.read_csv("benchmark_data.csv", parse_dates=["Date"], index_col=["Date"]).dropna()
    # 了解数据
    print("Stocks\n")
    print(stock_data.info())
    print(stock_data.head())
    print("\nBenchmarks\n")
    print(benchmark_data.info())
    print(benchmark_data.head())
    # 输出统计量
    print(stock_data.describe())
    print(benchmark_data.describe())
    # 计算每日回报率
    stock_returns = stock_data.pct_change()
    print(stock_returns.describe())
    sp_returns = benchmark_data.pct_change()
    print(sp_returns.describe())
    # 每日超额回报
    excess_returns = pd.DataFrame()
    risk_free = 0.04 / 252.0
    excess_returns["Amazon"] = stock_returns["Amazon"] - risk_free
    excess_returns["Facebook"] = stock_returns["Facebook"] - risk_free
    print(excess_returns.describe())
    # 超额回报的均值
    avg_excess_return = excess_returns.mean()
    print(avg_excess_return)
    # 超额回报的标准差
    std_excess_return = excess_returns.std()
    print(std_excess_return)
    # 计算夏普比率
    # 日夏普比率
    daily_sharpe_ratio = avg_excess_return.div(std_excess_return)
    # 年化夏普比率
    annual_factor = np.sqrt(252)
    annual_sharpe_ratio = daily_sharpe_ratio.mul(annual_factor)
    print("年化夏普比率\n", annual_sharpe_ratio)

    # 用empyrical算
    sharpe = pd.DataFrame()
    a = ey.sharpe_ratio(stock_returns["Amazon"], risk_free=risk_free)  # , annualization = 252)
    b = ey.sharpe_ratio(stock_returns["Facebook"], risk_free=risk_free)
    print("empyrical计算结果")
    print(a, b)
    print(a / annual_sharpe_ratio["Amazon"], b / annual_sharpe_ratio["Facebook"])


if __name__ == "__main__":
    # testpkg()
    testSharpe()
