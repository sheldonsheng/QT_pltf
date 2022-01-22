# -*-coding: utf-8 -*-
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tushare as ts
import dateutil
import datetime
import rqdatac as rq
from rqdatac import *


rq.init('15821345316', '19890915sxy')
# df = get_trading_dates(start_date='1990-01-01', end_date='2022-01-22')
# df = pd.DataFrame(df)
# df.to_csv('trade_cal.csv')


pro = ts.pro_api('7978c1192b900af6a5a83a9df017d364bc76db64ddda2f2548e7d3c0')
trade_cal = pd.read_csv('trade_cal.csv')


CASH = 100000
START_DATE = '2016-01-29'
END_DATE = '2016-09-21'


class Context:
    def __init__(self, cash, start_date, end_date):
        self.cash = cash
        self.start_date = start_date
        self.end_date = end_date
        self.positions = {}
        self.benchmark = None
        self.date_range = trade_cal[(trade_cal['calendarDate'] >= start_date) & \
                                    (trade_cal['calendarDate'] <= end_date)]['calendarDate'].values
        self.dt = None


context = Context(CASH, START_DATE, END_DATE)


class G:
    pass


g = G()


def attribute_history(security, count, fields=('open', 'close', 'high', 'low', 'vol')):
    end_date = (context.dt - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    start_date = trade_cal[trade_cal['calendarDate'] <= end_date][-count:].iloc[0, :]['calendarDate']
    return attribute_daterange_history(security, start_date, end_date, fields)


def attribute_daterange_history(security, start_date, end_date, fields=('open', 'close', 'high', 'low', 'vol')):
    try:
        f = open(security+'.csv', 'r')
        df = pd.read_csv(f, index_col='trade_date', parse_dates=['trade_date']).loc[start_date:end_date, :]
    except FileNotFoundError:
        df = pro.daily(ts_code=security + '.SH', start_date='start_date', end_date='end_date')

    return df[list(fields)]


def get_today_data(security):
    today = context.dt.strftime('%Y-%m-%d')
    try:
        f = open(security + '.csv', 'r')
        data = pd.read_csv(f, index_col='trade_date', parse_dates=['trade_date']).loc[today, :]
    except FileNotFoundError:
        data = pro.daily(ts_code=security + '.SH', start_date=today, end_date=today)
    except KeyError: #找不到这个东西
        data = pd.Series()
    return data


def _order(today_data, security, amount):
    p = today_data['open'].squeeze()
    if len(today_data) == 0:
        print("今日停牌")
        return

    if context.cash - amount * p < 0:
        amount = int(context.cash / p)
        print("现金不足,已调整为%d" % amount)

    if amount % 100 != 0:
        if amount != -context.positions.get(security, 0):
            amount = int(amount / 100) * 100
            print("不是100的倍数，已调整为%d" % amount)
        if context.positions.get(security, 0) < -amount:
            amount = -context.positions.get(security, 0)
            print("超过现有持仓，已调整为%d" % amount)

    context.positions[security] = context.positions.get(security, 0) + amount #更新仓位信息

    context.cash -= amount * p #更新资金信息

    if context.positions[security] == 0:
        del context.positions[security]


def order(security, amount):
    today_data = get_today_data(security)
    _order(today_data, security, amount)


def order_target(security, amount):
    if amount < 0:
        print("数量不能为负，已调整为0")
        amount = 0

    today_data = get_today_data(security)
    hold_amount = context.positions.get(security, 0)  # TODO: T+1 use closeable amount / total amount to solve this problem. #todo: positions should be squeezed?
    delta_amount = amount - hold_amount
    _order(today_data, security, delta_amount)


def order_value(security, value):
    today_data = get_today_data(security)
    amount = value / today_data['open'].squeeze()
    _order(today_data, security, amount)


def order_target_value(security, value):
    today_data = get_today_data(security)
    if value < 0:
        print("价值不能为负，已调整为0")
        value = 0

    hold_value = context.positions.get(security, 0) * today_data['open'].squeeze() #todo: positions should be squeezed?
    delta_value = (value - hold_value)
    order_value(security, delta_value)


def run():
    plt_df = pd.DataFrame(index=pd.to_datetime(context.date_range), columns=['value'])
    initialize(context)
    last_price = {}
    for dt in context.date_range:
        context.dt = dateutil.parser.parse(dt)
        handle_data(context)
        value = context.cash
        for stock in context.positions:
            today_data = get_today_data(stock)
            if len(today_data) == 0:
                p = last_price[stock]
                print(last_price)
            else:
                p = today_data(stock)['open']
                print(last_price)
            value += p * context.positions[stock]
        plt_df.loc[dt, 'value'] = value
    print(plt_df)


def initialize(context):
    pass


def handle_data(context):
    order('601318', 100)


run()

