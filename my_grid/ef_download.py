#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2025/7/3 22:13
# @Author  : david_van
# @Desc    :
import efinance as ef

from my_grid.get_1_mintus import get_quote_history_1_minute

stock_code = '300015'

frequency = 1
start_date = '20230101'
end_date = '20250630'

# df = ef.stock.get_quote_history(stock_code, beg=start_date, end=end_date, klt=frequency)
# df.to_csv(f'{stock_code}_{frequency}_{start_date}.csv', index=False, encoding='utf-8')  # 避免中文乱码
df = get_quote_history_1_minute(stock_code, start_date)
df.to_csv(f'{stock_code}_{frequency}_{start_date}.csv', index=False, encoding='utf-8')  # 避免中文乱码
