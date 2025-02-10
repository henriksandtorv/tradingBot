from datetime import datetime
from lumibot.backtesting import YahooDataBacktesting
from lumibot.credentials import IS_BACKTESTING
from lumibot.strategies import Strategy
from lumibot.traders import Trader
import numpy as np
import pandas as pd


class Trend(Strategy):
    parameters = {
        "symbol" : "SPY",
        "quantity" : None
    }

    def initialize(self):
        self.vars.signal = None
        self.vars.start = "2022-01-01"
        self.sleeptime = "1D"
    
    def on_trading_iteration(self):

        bars = self.get_historical_prices(self.parameters['symbol'], 22, "day")
        gld = bars.df
        gld['9-day'] = gld['close'].rolling(9).mean()
        gld['21-day'] = gld['close'].rolling(21).mean()
        gld['Signal'] = np.where(np.logical_and(gld['9-day'] > gld['21-day'],
                                                gld['9-day'].shift(1) < gld['21-day'].shift(1)),
                                 "BUY", None)
        gld['Signal'] = np.where(np.logical_and(gld['9-day'] < gld['21-day'],
                                                gld['9-day'].shift(1) > gld['21-day'].shift(1)),
                                 "SELL", gld['Signal'])
        self.vars.signal = gld.iloc[-1].Signal
        
        symbol = self.parameters['symbol']
        price = self.get_last_price(symbol)
        cash = self.get_cash()
        quantity = cash * .5 // price
        if self.vars.signal == 'BUY':
            pos = self.get_position(symbol)
            if pos:
                self.sell_all()
                
            order = self.create_order(symbol, quantity, "buy")
            self.submit_order(order)

        symbol = self.parameters['symbol']
        position = self.get_position(symbol)
        if position:
            current_price = self.get_last_price(symbol)
            stop_loss_price = current_price * 0.99  # 1% stop loss
            take_profit_price = current_price * 1.01  # 1% take profit
            if current_price <= stop_loss_price:
                self.sell_all()
            elif current_price >= take_profit_price:
                self.sell_all()
            elif self.vars.signal == 'SELL':
                pos = self.get_position(symbol)
                if pos:
                    self.sell_all()
                cash = self.get_cash()
                quantity = cash * .5 // price    
                order = self.create_order(symbol, quantity, "sell")
                self.submit_order(order)

if __name__ == "__main__":

    if not IS_BACKTESTING:
        strategy = Trend()
        bot = Trader()
        bot.add_strategy(strategy)
        bot.run_all()
    else:
        start = datetime(2024, 5, 14)
        end = datetime(2024, 11, 14)
        Trend.backtest(
            YahooDataBacktesting,
            start,
            end,
            benchmark_asset= "NVDA"
        )