#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2025/7/1 07:04
# @Author  : david_van
# @Desc    :
# 导入相关库
import os

import backtrader as bt
import pandas as pd
import datetime
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'Alibaba PuHuiTi 2.0'
plt.rcParams['axes.unicode_minus'] = False  # 设置字体
# 数据样本
_data_root = r'D:\code\pycharm\test\grid-trading-system\mnt\data'
file_name = 'sz002381.xlsx'
data_path = os.path.join(_data_root, file_name)
print(f'data_path is {data_path}')

df = pd.read_excel(data_path, header=2).rename(columns=lambda x: x.strip())
# 调整数据clumns，且按照时间升序
#       时间	    开盘	    最高	    最低	    收盘	         成交量
df['openinterest'] = 0  # 添加一列数据
# data = df.loc[:, ['open', 'high', 'low', 'close', 'vol', 'openinterest', 'trade_date']]  # 选择需要的数据
# df = df.loc[2:]
data = df.loc[:, ['时间', '开盘', '最高', '最低', '收盘', '成交量', 'openinterest']]  # 选择需要的数据
data.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume', 'openinterest']  # 修改列名
data = data.set_index(
    pd.to_datetime(data['datetime'].astype('str'), errors='coerce')).sort_index()  # 把datetime列改为时间格式并排序
# 这个数据是整理过的，实际操作中可能会有一下缺失数据，所以需要做一下填充。
data.loc[:, ['volume', 'openinterest']] = data.loc[:, ['volume', 'openinterest']].fillna(0)
data.loc[:, ['open', 'high', 'low', 'close']] = data.loc[:, ['open', 'high', 'low', 'close']].fillna(method='pad')
cerebro = bt.Cerebro()  # 引入大脑，并实例化
datafeed = bt.feeds.PandasData(dataname=data,  # 导入前面整理好的pddata数据
                               fromdate=datetime.datetime(2024, 1, 1),  # 起始时间
                               todate=datetime.datetime(2025, 5, 31))  # 结束时间
cerebro.adddata(datafeed, name='000155')  # 通过cerebro.adddata添加给大脑，并通过 name赋值 实现数据集与股票的一一对应
print('读取成功')
cerebro.broker.setcash(20000.0)  # 设置起始资金


class bollqt(bt.Strategy):  # bollqt为此策略的名称，为自定义。
    def __init__(self):  # 全局只调用一次，一般在此函数中计算指标数据。
        self.B = bt.ind.BBands(self.data0.close, period=20)  # 这是backtrader中自带的指标计算函数，也可以用talib计算。
        # 方式为self.xx=bt.talib.指标代号(‘计算的基础数据，如收盘价’,timeperiod=‘计算参数’)

    def next(self):
        # 计算买卖条件
        if self.getposition(self.data).size == 0:  # 通过此函数查询持仓，若持仓等于0
            if self.B.bot[0] > self.data.close[0] and self.B.bot[-1] < self.data.close[-1]:  # 当前一日接近下轨，当日跌破下轨时买入
                self.order = self.buy(self.data, 100)  # 买入100股
                print('买入成功')
            else:
                print('不符合入场条件')
        elif self.getposition(self.data).size > 0:  # 持仓大于0时
            if self.B.top[0] < self.data.close[0] and self.B.top[-1] > self.data.close[-1]:  # 前一期小于上轨，当日突破上轨卖出
                self.order = self.close(self.data, 100)  # 平仓100股
                print('卖出成功')
            else:
                print('不符合卖出条件')


# cerebro.broker.setcash(1000000.0)  # 设置起始资金
cerebro.addstrategy(bollqt)  # 把策略添加给大脑
cerebro.run()  # 运行

if __name__ == '__main__':
    print(123)
