#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2025/7/5 11:11
# @Author  : david_van
# @Desc    :

# config.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Type

import backtrader as bt


@dataclass
class BackTestConfig:
    """
    回测配置类，用于定义回测参数
    """

    strategy: Type[bt.Strategy]  # 使用的策略类
    start: datetime | None  # 回测开始时间
    end: datetime | None  # 回测结束时间
    code: List[str]  # 股票代码列表
    name: List[str]  # 股票名称列表（需与 code 对应）
    file_name: List[str]  # 文件名列表
    cash: float = 100000  # 初始资金，默认 100000
    benchmark_code: str = "510300"  # 基准指数代码
    draw_plot: bool = True,  # 是否绘制图表
    grid_params: dict = field(default_factory=dict)

    def __post_init__(self):
        """
        初始化后校验
        """
        # 校验策略是否是 bt.Strategy 的子类
        if not issubclass(self.strategy, bt.Strategy):
            raise TypeError("strategy 必须是 backtrader.Strategy 的子类")

        # 校验 code 和 name 长度一致
        if len(self.code) != len(self.name):
            raise ValueError("code 和 name 列表长度必须一致")

        # 校验现金不能为负数
        if self.cash < 0:
            raise ValueError("cash 不能为负数")

        # 校验起始时间不能晚于结束时间
        if self.start is not None and self.end is not None:
            if self.start >= self.end:
                raise ValueError(f"start 时间不能晚于 end 时间: start={self.start}, end={self.end}")

@dataclass(init=False)
class OrderRecord:
    trade_time: datetime  # 交易时间
    trade_direction: str  # 交易方向
    set_price: float  # 设定价格
    deal_price: float  # 成交价格
    deal_quantity: int  # 成交数量
    deal_amount: float  # 成交金额
    commission: float  # 手续费

    def __init__(self, trade_time, deal_price, set_price, deal_quantity, deal_amount, commission,
                 trade_direction: str = None):
        # 在对象创建后对浮点数字段进行格式化
        self.trade_time = trade_time
        self.trade_direction = trade_direction
        self.deal_price = round(deal_price, 3)
        self.set_price = round(set_price, 3)
        self.deal_quantity = deal_quantity
        self.deal_amount = round(deal_amount, 3)
        self.commission = round(commission, 3)