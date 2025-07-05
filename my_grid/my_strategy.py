import backtrader as bt


# 网格策略
class GridStrategy(bt.Strategy):
    params = (
        ("printlog", True),
        ("top", 20),
        ("buttom", 10),
    )

    def __init__(self):
        # self.mid = (self.p.top + self.p.buttom) / 2.0
        # # 百分比区间计算
        # # 这里多1/2，是因为arange函数是左闭右开区间。
        # perc_level = []
        # for x in np.arange(1 + 0.02 * 5, 1 - 0.02 * 5 - 0.02 / 2, -0.02):
        #     perc_level.append(x)
        # # 价格区间
        # # print(self.mid)
        # self.price_levels = [self.mid * x for x in perc_level]
        grid_prices = []
        step_percent = 0.1

        current_price = self.p.top
        while current_price >= self.p.buttom:
            grid_prices.append(current_price)
            current_price = round(current_price * (1 - step_percent), 2)
        self.price_levels = grid_prices
        # 记录上一次穿越的网格
        self.last_price_index = None
        # 总手续费
        self.comm = 0.0

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
                if self.data.close[0] > self.price_levels[i]:
                    self.last_price_index = i
                    self.order_target_percent(target=i / (len(self.price_levels) - 1))
                    print("开仓")
                    return
        # 调仓
        else:
            signal = False
            buy = False
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
                    self.order = self.sell(size=200, price=upper, exectype=bt.Order.Limit)
                    continue
                # 还不是最重仓，继续跌，再买一档
                if lower != None and self.data.close[0] < lower:
                    self.last_price_index = self.last_price_index + 1
                    signal = True
                    self.order = self.buy(size=200, price=lower, exectype=bt.Order.Limit)
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
                    f'执行卖出,时间为：{bt.num2date(order.executed.dt).isoformat()} 价格: %.2f, 成本: %.2f, 手续费 %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

            self.comm += order.executed.comm
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("交易失败")
            self.order = None
        else:
            self.log("未知状态交易失败")
            self.order = None

    # 输出手续费
    def stop(self):
        self.log("手续费:%.2f 成本比例:%.5f" % (self.comm, self.comm / self.broker.getvalue()))
