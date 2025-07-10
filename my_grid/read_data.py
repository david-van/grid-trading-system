#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2025/7/5 10:14
# @Author  : david_van
# @Desc    :
import datetime
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pandas.core.frame import DataFrame


def get_project_root() -> str:
    current_dir = os.path.abspath(os.path.dirname(__file__))
    while not os.path.exists(os.path.join(current_dir, 'requirements.txt')):
        current_dir = os.path.dirname(current_dir)
    return current_dir


# 获取项目根目录
project_root = get_project_root()
print(f"项目根目录是: {project_root}")


def get_all_time_data(file_name: str, file_path: str = r'data') -> DataFrame:
    _data_root = os.path.join(project_root, file_path)
    # file_name = 'sz.300363_60_2023-01-01.csv'
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


def get_data_by_date(file_name: str, start_time: datetime.datetime, end_time: datetime.datetime,
                     file_path=r'data') -> DataFrame:
    data = get_all_time_data(file_name, file_path)
    filtered = data.loc[start_time:end_time]
    return filtered


class MergeIndex:
    def merge_data(self):
        # 读取csv文件
        pb_file_name = r'data/Index/pb/证券公司_PB_市值加权_上市以来_20250710_072405.csv'
        index_file_name = r'data/Index/points/399975_101_20140101.csv'
        pb_data_path = os.path.join(project_root, pb_file_name)
        index_data_path = os.path.join(project_root, index_file_name)
        pb = pd.read_csv(os.path.join(project_root, pb_file_name))
        index = pd.read_csv(os.path.join(project_root, index_file_name))
        pb = pb.loc[:,
             ["日期", "收盘点位", "PB市值加权", "PB 分位点", "PB 80%分位点值", "PB 50%分位点值", "PB 20%分位点值"]]
        pb = pb.rename(columns={
            'PB 80%分位点值': 'PB_80',
            'PB 50%分位点值': 'PB_50',
            'PB 20%分位点值': 'PB_20',
        })
        pb['pb_value'] = pb['PB市值加权'].astype(str).str.lstrip("=")
        pb['PB_80'] = pb['PB_80'].astype(str).str.lstrip("=")
        pb['PB_50'] = pb['PB_50'].astype(str).str.lstrip("=")
        pb['PB_20'] = pb['PB_20'].astype(str).str.lstrip("=")
        # for row in pb.itertuples():
        #     print(row.datetime, row.open, row.close)

        # 确保日期列是datetime类型
        pb['date'] = pd.to_datetime(pb['日期'], errors='coerce')
        index['date'] = pd.to_datetime(index['日期'], errors='coerce')
        pb = pb.drop('日期', axis=1)
        index = index.drop('日期', axis=1)

        # 根据日期合并数据集
        df: pd.DataFrame = pd.merge(index, pb, on='date', how='left')

        # 设置 date 为索引
        df.set_index(keys=['date'])

        # 按照 252 * 3 天窗口计算 pb 的滚动百分位
        pb_point = df['pb_value']
        df['pb_percentile'] = pb_point.rolling(window=252 * 3, min_periods=1).apply(
            lambda x: pd.Series(x).rank(pct=True).iloc[-1].round(4)
        )
        # 2. 计算当前滚动窗口中 PB 的 20% 分位值
        df['pb_20th_percentile'] = pb_point.rolling(window=252 * 3, min_periods=1).apply(
            lambda x: np.percentile(x, 20)
        ).round(4)
        df['pb_50th_percentile'] = pb_point.rolling(window=252 * 3, min_periods=1).apply(
            lambda x: np.percentile(x, 50)
        ).round(4)
        df['pb_80th_percentile'] = pb_point.rolling(window=252 * 3, min_periods=1).apply(
            lambda x: np.percentile(x, 80)
        ).round(4)

        csv_filename = '证券公司_399975_PB.csv'
        df.to_csv(csv_filename, index=False, encoding='utf-8')

    def data_show(self, df: pd.DataFrame = None):
        index_file_name = r'my_grid/证券公司_399975_PB.csv'
        df = pd.read_csv(os.path.join(project_root, index_file_name))
        # 绘制折线图
        plt.figure(figsize=(12, 6))

        # 绘制每一条百分位列
        plt.plot(df.index, df['pb_percentile'], label='PB Percentile')
        plt.plot(df.index, df['pb_20th_percentile'], label='PB 20th Percentile')
        plt.plot(df.index, df['pb_50th_percentile'], label='PB 50th Percentile')
        plt.plot(df.index, df['pb_80th_percentile'], label='PB 80th Percentile')
        # 绘制点位图
        plt.plot(df.index, df['收盘'], 'o', label='Close Points')

        # 添加标题和标签
        plt.title('Percentile Lines')
        plt.xlabel('Date')
        plt.ylabel('Values')
        plt.legend()  # 显示图例

        # 展示图表
        plt.show()


def merge_index_data():
    merge_index = MergeIndex()
    merge_index.merge_data()


def merge_index_data_show():
    merge_index = MergeIndex()
    merge_index.data_show()


def test_get_data():
    file_name = 'sz.300363_60_2023-01-01.csv'
    start_time = datetime.datetime(2023, 1, 1)
    end_time = datetime.datetime(2023, 1, 6)
    print(type(start_time))
    data = get_data_by_date(file_name, start_time, end_time)
    print(data)


if __name__ == '__main__':
    # test_get_data()
    # merge_index_data()
    merge_index_data_show()
