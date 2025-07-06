#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2025/7/5 14:17
# @Author  : david_van
# @Desc    :
import backtrader as bt
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
import pyfolio as pf
import quantstats as qs
# 正常显示画图时出现的中文和负号
from pylab import mpl

mpl.rcParams['font.sans-serif'] = ['SimHei']


class PerformanceVisualizer:
    """
    静态方法工具类，用于可视化策略绩效。
    """

    @staticmethod
    def plot_performance(pnl: pd.Series):
        """
        静态方法：绘制策略绩效图表，包括累计收益、回撤和绩效指标表格。

        参数:
        - pnl (pd.Series): 策略每日收益率序列
        """
        # 计算累计收益
        cumulative = (pnl + 1).cumprod()
        # 计算回撤
        max_return = cumulative.cummax()
        drawdown = (cumulative - max_return) / max_return

        # 计算年度和整体绩效指标
        perf_stats_year = pnl.groupby(pnl.index.to_period('Y')).apply(
            lambda data: pf.timeseries.perf_stats(data)
        ).unstack()
        perf_stats_all = pf.timeseries.perf_stats(pnl).to_frame(name='all')
        perf_stats = pd.concat([perf_stats_year, perf_stats_all.T], axis=0)
        perf_stats_ = round(perf_stats, 4).reset_index()

        # 设置绘图风格
        plt.rcParams['axes.unicode_minus'] = False
        plt.style.use('dark_background')

        fig, (ax0, ax1) = plt.subplots(2, 1, gridspec_kw={'height_ratios': [1.5, 4]}, figsize=(20, 8))
        cols_names = ['date', 'Annual\nreturn', 'Cumulative\nreturns', 'Annual\nvolatility',
                      'Sharpe\nratio', 'Calmar\nratio', 'Stability', 'Max\ndrawdown',
                      'Omega\nratio', 'Sortino\nratio', 'Skew', 'Kurtosis', 'Tail\nratio',
                      'Daily value\nat risk']

        # 绘制绩效表格
        ax0.set_axis_off()
        table = ax0.table(cellText=perf_stats_.values,
                          bbox=(0, 0, 1, 1),
                          rowLoc='right',
                          cellLoc='right',
                          colLabels=cols_names,
                          colLoc='right',
                          edges='open')
        table.set_fontsize(13)

        # 双轴绘图
        ax2 = ax1.twinx()
        ax1.yaxis.set_ticks_position('right')
        ax2.yaxis.set_ticks_position('left')

        # 回撤曲线
        drawdown.plot.area(ax=ax1, label='drawdown (right)', alpha=0.3, fontsize=13, grid=False)
        # 累计收益曲线
        cumulative.plot(ax=ax2, color='#F1C40F', lw=3.0, label='cumret (left)', fontsize=13, grid=False)

        # x轴设置
        ax2.set_xbound(lower=cumulative.index.min(), upper=cumulative.index.max())
        ax2.xaxis.set_major_locator(ticker.MultipleLocator(100))

        # 图例合并显示
        h1, l1 = ax1.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        plt.legend(h1 + h2, l1 + l2, fontsize=12, loc='upper left', ncol=1)

        fig.tight_layout()
        plt.show()

    @staticmethod
    def draw_result(cerebro: bt.Cerebro) -> None:
        cerebro.plot(numfigs=1)
        plt.savefig(f"result.png")

    @classmethod
    def show_by_pyfolio(cls, pyfoliozer: bt.analyzers.PyFolio):
        returns, positions, transactions, glev = pyfoliozer.get_pf_items()
        # pf.create_full_tear_sheet(
        #     returns,
        #     positions=positions,
        #     transactions=transactions,
        #     # gross_lev=gross_lev,
        #     round_trips=False)
        # 强制转换类型
        # print(f'returns type is {type(returns)}')
        # print(f'returns.head() = \n{returns.head()}')
        # print(f'returns.empty = {returns.empty}')
        # print(f'returns.index = {returns.index}')
        #
        # if not isinstance(returns, pd.Series):
        #     print(f'returns is {returns}')
        #     returns = pd.Series(returns)
        # returns.index = returns.index.tz_convert(None)
        # 显式转换 returns 为标准 Series，并重置索引以避免潜在问题
        # returns = pd.Series(returns.values, index=returns.index)
        #
        # # 或者强制转换为 DataFrame 再处理
        # returns_df = pd.DataFrame({'return': returns})
        # returns = returns.tz_convert(None)
        # 基础报告（HTML格式）
        qs.reports.html(returns, output='quantstats_report.html', title='策略绩效')
        # qs.reports.basic(returns)
