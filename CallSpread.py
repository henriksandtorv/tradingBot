import calendar
from datetime import datetime, timedelta
from lumibot.backtesting import BacktestingBroker, PolygonDataBacktesting, YahooDataBacktesting
from lumibot.credentials import IS_BACKTESTING
from lumibot.strategies import Strategy
from lumibot.entities import Asset
from lumibot.traders import Trader

class CallSpread(Strategy):
    parameters = {
        "symbol": "SPY",
        "Quantity": 10,
        "Spread_size": 5,
        "delta" : 1
    }

    def initialize(self):
        self.sleeptime = "1D"

    def on_trading_iteration(self):
        date = self.get_datetime().replace(tzinfo=None).date()
        exp = self.get_next_exp(date)
        price = self.get_last_price(self.parameters["symbol"])
        size = self.parameters["Quantity"]
        strike_low, strike_high = self.calc_strikes(price, size)
        delta = timedelta(days=self.parameters["delta"])
        close = exp - delta
        self.log_message(f"Current price: {price}")
        self.log_message(f"Low strike: {strike_low}, High strike: {strike_high}")
        self.log_message(f"Expiration: {exp}")

        long_call = Asset(
            symbol=self.parameters["symbol"],
            asset_type = Asset.AssetType.OPTION,
            expiration=exp,
            strike=strike_high,
            right=Asset.OptionRight.CALL, 
        )

        positions = len(self.get_positions())
        if positions <= 1:
            quantity = self.parameters["Quantity"]
            orders = [
                self.create_order(long_call, quantity, "buy"),
                self.create_order(long_call, quantity, "sell"),
            ]

            for order in orders:
                self.submit_order(order)
        
        if date == close:
            exp = self.get_next_exp(date)
            self.sell_all()
    
    def find_strike(self, price, base = 5):
        return round(price / base) * 5
    
    def calc_strikes(self, price, spread_size = 5):
        atm = self.find_strike(price)
        return atm, atm + spread_size

    def get_next_exp(self, date):
        first_friday = 0

        if date.month == 12:
            year = date.year + 1
        else:
            year = date.year
        if date.month == 12:
            month = (date.month + 1) % 12
        else:
            month = date.month + 1
        
        next_month = calendar.monthcalendar(year, month)
        for week in next_month:
            for day in week:
                if day > 0 and calendar.weekday(year, month, day) == calendar.FRIDAY:
                    first_friday = day
                    break
            if first_friday:
                break
        return datetime(year, month, first_friday + 14).date()
    
if __name__ == "__main__":

    if not IS_BACKTESTING:
        strategy = CallSpread()
        bot = Trader()
        bot.add_strategy(strategy)
        bot.run_all()
    else:
        start = datetime(2024, 1, 1)
        end = datetime(2024, 11, 24)
        CallSpread.backtest(
            YahooDataBacktesting,
            start,
            end,
            benchmark_asset= "SPY"
        )