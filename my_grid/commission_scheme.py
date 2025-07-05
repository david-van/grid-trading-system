#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2025/7/5 10:11
# @Author  : david_van
# @Desc    :

import backtrader as bt


class StockCommission(bt.CommInfoBase):
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
