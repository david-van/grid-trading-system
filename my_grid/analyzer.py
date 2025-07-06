#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2025/7/5 12:13
# @Author  : david_van
# @Desc    : 该类用于计算和分析投资策略的风险指标

import empyrical as ey
import numpy as np
import pandas as pd


class RiskAnalyzer:
    """
    RiskAnalyzer类用于计算投资策略的风险指标。
        用empyrical库计算风险指标
    参数:
    - returns: pd.Series, 投资策略的收益序列
    - bench_returns: pd.Series, 基准策略的收益序列
    - risk_free_rate: float, 无风险利率，默认为0.02
    """

    def __init__(self, returns: pd.Series, bench_returns: pd.Series, risk_free_rate: float = 0.02):
        self.__returns = returns
        self.__bench_returns = bench_returns
        self.__risk_free = risk_free_rate
        self.__alpha = 0.0
        self.__beta = 0.0
        self.__info = 0.0
        self.__vola = 0.0
        self.__omega = 0.0
        self.__sharpe = 0.0
        self.__sortino = 0.0
        self.__calmar = 0.0

    def run(self) -> pd.Series:
        """
        计算所有风险指标，并返回包含这些指标的Series。

        返回:
        - pd.Series, 包含所有风险指标的Series
        """
        # 计算各指标
        # self._alpha_beta()
        # self._info()
        self._vola()
        self._omega()
        self._sharpe()
        self._sortino()
        self._calmar()
        result_dict = {
            # "阿尔法": self.__alpha,
            # "贝塔": self.__beta,
            # "信息比例": self.__info,
            "策略波动率": self.__vola,
            "欧米伽": self.__omega,
            "夏普值": self.__sharpe,
            "sortino": self.__sortino,
            "calmar": self.__calmar
        }
        return pd.Series(result_dict)

    def _alpha_beta(self):
        """
        计算阿尔法和贝塔值。

        阿尔法表示投资策略的超额回报，贝塔值表示投资策略对市场波动的敏感度。
        """
        self.__alpha, self.__beta = ey.alpha_beta(returns=self.__returns, factor_returns=self.__bench_returns,
                                                  risk_free=self.__risk_free, annualization=1)

    def _info(self):
        """
        计算信息比例。

        信息比例衡量的是投资策略相对于基准策略的超额回报与其跟踪误差的比率。
        """
        self.__info = ey.excess_sharpe(returns=self.__returns, factor_returns=self.__bench_returns)

    def _vola(self):
        """
        计算策略波动率。

        波动率衡量的是投资策略收益的波动程度。
        """
        self.__vola = ey.annual_volatility(self.__returns, period='daily')

    def _omega(self):
        """
        计算欧米伽比率。

        欧米伽比率衡量的是投资策略收益超过目标收益的部分与未超过部分的比率。
        """
        self.__omega = ey.omega_ratio(returns=self.__returns, risk_free=self.__risk_free)

    def _sharpe(self):
        """
        计算夏普比率。

        夏普比率衡量的是投资策略每承受一单位总风险，能产生的超额回报。
        """
        self.__sharpe = ey.sharpe_ratio(returns=self.__returns, annualization=1)

    def _sortino(self):
        """
        计算索提诺比率。

        索提诺比率衡量的是投资策略每承受一单位下行风险，能产生的超额回报。
        """
        self.__sortino = ey.sortino_ratio(returns=self.__returns,
                                          required_return=self.__risk_free/252,  # 才是目标回报率
                                          # annualization=252  # 日频数据常用252天进行年化
                                          )

    def _calmar(self):
        """
        计算卡玛比率。

        卡玛比率衡量的是投资策略的复合年化收益率与其最大回撤的比率。
        """
        self.__calmar = ey.calmar_ratio(returns=self.__returns)


class IndicatorAnalyzer:
    def judge_by_SQN(sqn: float) -> str:
        # 根据SQN值对策略做出评估
        # 按照backtrader文档写的
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
        return result


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
