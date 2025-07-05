#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2025/7/5 10:14
# @Author  : david_van
# @Desc    :
import datetime
import os

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


if __name__ == '__main__':
    file_name = 'sz.300363_60_2023-01-01.csv'
    start_time = datetime.datetime(2023, 1, 1)
    end_time = datetime.datetime(2023, 1, 6)
    print(type(start_time))
    data = get_data_by_date(file_name, start_time, end_time)
    print(data)
