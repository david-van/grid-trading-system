from dataclasses import dataclass

import backtrader as bt
import pandas as pd
from datetime import datetime


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


class MergeIndex:
    def merge_data(self):
        # 读取csv文件
        pb = pd.read_csv(
            r'D:\code\pycharm\test\grid-trading-system\data\Index\pb\证券公司_PB_市值加权_上市以来_20250710_072405.csv')
        index = pd.read_csv(r'D:\code\pycharm\test\grid-trading-system\data\Index\points\399975_101_20140101.csv')
        pb = pb.loc[:, ["日期", "收盘点位", "PB 分位点", "PB 80%分位点值", "PB 50%分位点值", "PB 20%分位点值"]]
        # 确保日期列是datetime类型
        pb['date'] = pd.to_datetime(pb['日期'], errors='coerce')
        index['date'] = pd.to_datetime(index['日期'], errors='coerce')
        pb = pb.drop('日期', axis=1)
        index = index.drop('日期', axis=1)

        # 根据日期合并数据集
        df = pd.merge(index, pb, on='date', how='left')
        csv_filename = '证券公司_399975_PB.csv'
        df.to_csv(csv_filename, index=False, encoding='utf-8')



if __name__ == '__main__':
    merge_index = MergeIndex()
    merge_index.merge_data()


# 网格策略
class GridStrategy(bt.Strategy):
    params = (
        ("printlog", True),
        ("top", None),
        ("bottom", None),
        ("step_percent", None),
    )

    def __init__(self, *args, **kwargs):
        params_dict = dict(self.p._getkwargs())
        print(f'params is {params_dict}')
        # self.mid = (self.p.top + self.p.bottom) / 2.0
        # # 百分比区间计算
        # # 这里多1/2，是因为arange函数是左闭右开区间。
        # perc_level = []
        # for x in np.arange(1 + 0.02 * 5, 1 - 0.02 * 5 - 0.02 / 2, -0.02):
        #     perc_level.append(x)
        # # 价格区间
        # # print(self.mid)
        # self.price_levels = [self.mid * x for x in perc_level]
        grid_prices = []

        current_price = self.p.top
        while current_price >= self.p.bottom:
            grid_prices.append(current_price)
            current_price = round(current_price * (1 - self.p.step_percent), 2)
        self.price_levels = grid_prices
        # 记录上一次穿越的网格
        self.last_price_index = None
        # 总手续费
        self.comm = 0.0
        self.total_value = args[0]
        self.trade_record = []

    def next(self):
        # print('当前可用资金', self.broker.getcash())
        # print('当前总资产', self.broker.getvalue())
        # print('当前持仓量', self.broker.getposition(self.data).size)
        # print('当前持仓成本', self.broker.getposition(self.data).price)
        # print(self.last_price_index)
        # 开仓
        if self.last_price_index == None:
            print(f"价格区间为：{self.price_levels}")
            for i in range(len(self.price_levels)):
                price = self.data.close[0]
                # print("c", i, price, self.price_levels[i][0])
                if price > self.price_levels[i]:
                    self.last_price_index = i
                    # self.order_target_percent(target=i / (len(self.price_levels) - 1))
                    break
            if self.last_price_index > 0:
                for i in range(self.last_price_index):
                    self.sell(size=200, price=self.price_levels[i], exectype=bt.Order.Market)
                print("开仓.......")
        # 调仓
        else:
            signal = False
            buy_index = 0
            while True:
                upper = None
                lower = None
                if self.last_price_index > 0:
                    upper = self.price_levels[self.last_price_index - 1]
                if self.last_price_index < len(self.price_levels) - 1:
                    lower = self.price_levels[self.last_price_index + 1]
                # 还不是最轻仓，继续涨，再卖一档
                if upper != None and self.data.close[0] > upper:
                    self.last_price_index = self.last_price_index - 1
                    signal = True
                    self.order = self.sell(size=200, price=upper, exectype=bt.Order.Market)
                    continue
                # 还不是最重仓，继续跌，再买一档
                if lower != None and self.data.close[0] < lower:
                    self.last_price_index = self.last_price_index + 1
                    signal = True
                    self.order = self.buy(size=200, price=lower, exectype=bt.Order.Market)
                    continue
                break
            if signal:
                self.long_short = None
                # self.order_target_percent(target=self.last_price_index / (len(self.price_levels) - 1))
                # if buy:
                #     self.order = self.buy(size=200)
                # else:
                #     self.order = self.sell(size=200)

    # 输出交易记录
    def log(self, txt, dt=None, doprint=False):
        if self.p.printlog or doprint:
            dt = dt or self.data.datetime.datetime(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def notify_order(self, order):
        # self.log(
        #     f'记录日志,时间为：{bt.num2date(self.data.datetime[0]).isoformat()} order.status is {order.status} ')

        # 有交易提交/被接受，啥也不做
        if order.status in [order.Submitted, order.Accepted]:
            return
        # 交易完成，报告结果
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f'执行买入,时间为：{bt.num2date(order.executed.dt).isoformat()} 价格: %.2f, 成本: %.2f, 手续费 %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))
                self.buyprice = order.executed.price
            elif order.issell():
                self.log(
                    f'执行卖出,时间为：{bt.num2date(order.executed.dt).isoformat()} 价格: %.2f, 成本: %.2f,pnl: %.2f, 手续费 %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.pnl,
                     order.executed.comm))
            else:
                self.log(f'error:存在未知的情况')

            self.comm += order.executed.comm
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            # todo 优化此处的代码
            # self.log("交易失败，回滚索引位")
            # 回滚索引
            if order.executed.remsize is not None:
                count = int(order.executed.remsize / 200)
                if order.isbuy():
                    self.last_price_index = self.last_price_index - count
                elif order.issell():
                    self.last_price_index = self.last_price_index + count
                else:
                    self.log(f'error:存在未知的情况')
            else:
                self.log(f'error:存在获取不到买入/卖出数量的情况')
            self.order = None
        else:
            self.log("error:未知状态交易失败")
            self.order = None

    # 输出手续费
    def stop(self):
        self.log("手续费:%.2f 成本比例:%.5f" % (self.comm, self.comm / self.broker.getvalue()))
        for order in self.broker.orders:
            order_record = OrderRecord(
                trade_time=bt.num2date(order.executed.dt),
                set_price=order.created.price,
                deal_price=order.executed.price,
                deal_amount=order.executed.price * order.executed.size,
                deal_quantity=order.executed.size,
                commission=order.executed.comm
            )
            if order.isbuy():
                order_record.trade_direction = 'buy'
                self.total_value -= order_record.deal_amount
            else:
                order_record.trade_direction = 'sell'
                self.total_value += abs(order_record.deal_amount)
            self.trade_record.append(order_record)

        self.total_value -= self.comm
        print(f"当前value is {self.broker.get_value()},计算total_value is {self.total_value}")
        # 将数据转换为DataFrame
        df = pd.DataFrame([order.__dict__ for order in self.trade_record])

        # 将DataFrame写入CSV文件
        csv_filename = 'orders.csv'
        df.to_csv(csv_filename, index=False, encoding='utf-8')
