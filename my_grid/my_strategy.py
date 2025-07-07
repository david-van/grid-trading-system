import backtrader as bt


# 网格策略
class GridStrategy(bt.Strategy):
    params = (
        ("printlog", True),
        ("top", None),
        ("bottom", None),
        ("step_percent", None),
    )

    def __init__(self):
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
            if self.last_price_index > 0 :
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
