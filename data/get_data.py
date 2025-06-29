#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2025/6/29 19:17
# @Author  : david_van
# @Desc    :
import akshare as ak
import pandas as pd

# 示例：获取股票历史数据
df = ak.stock_zh_a_hist(symbol="000001", period="daily", adjust="hfq")

# 保存到Excel（默认Sheet1，不保留索引）
df.to_excel("stock_data.xlsx", index=False)  # [4,7](@ref)