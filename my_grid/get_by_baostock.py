#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2025/7/3 23:16
# @Author  : david_van
# @Desc    :
import baostock as bs
import pandas as pd

#### 登陆系统 ####
lg = bs.login()
# 显示登陆返回信息
print('login respond error_code:' + lg.error_code)
print('login respond  error_msg:' + lg.error_msg)

stock_code = 'sz.399975'

frequency = 'd'
start_date = '2012-06-01'
start_date = '2010-01-01'
start_date = '2016-01-01'
start_date = '2020-07-01'
start_date = '2017-01-01'
end_date = '2025-06-30'

#### 获取沪深A股历史K线数据 ####
# 详细指标参数，参见“历史行情指标参数”章节；“分钟线”参数与“日线”参数不同。“分钟线”不包含指数。
# 分钟线指标：date,time,code,open,high,low,close,volume,amount,adjustflag
# 周月线指标：date,code,open,high,low,close,volume,amount,adjustflag,turn,pctChg
# "date,code,open,high,low,close,preclose,volume,amount,pctChg"
stock_min_fields = "date,time,code,open,high,low,close,volume,amount,adjustflag"
day_fields = "date,code,open,high,low,close,preclose,volume,amount,turn,pctChg,peTTM,pbMRQ"
rs = bs.query_history_k_data_plus(stock_code, day_fields,
                                  start_date=start_date, end_date=end_date,
                                  frequency=frequency, adjustflag="3")
print('query_history_k_data_plus respond error_code:' + rs.error_code)
print('query_history_k_data_plus respond  error_msg:' + rs.error_msg)

#### 打印结果集 ####
data_list = []
while (rs.error_code == '0') & rs.next():
    # 获取一条记录，将记录合并在一起
    data_list.append(rs.get_row_data())
result = pd.DataFrame(data_list, columns=rs.fields)

#### 结果集输出到csv文件 ####
result.to_csv(f'{stock_code}_{frequency}_{start_date}.csv', index=False, encoding='utf-8')
print(result)

#### 登出系统 ####
bs.logout()
