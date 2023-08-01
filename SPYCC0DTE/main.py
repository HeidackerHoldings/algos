from AlgorithmImports import *
from datetime import timedelta, date


"""
TODO

Implement trailing stop loss for all SPY positions (3%)

Add parameters
    - Sell delay
    - Expiration
    - strikes
    - Stop loss percentage

Fix insufficient buying power orders/issues
Selling covered call vs buying it?
- Try self.Sell or self.MarketOrder(o, -volume)
Only use 90% of available cash?
"""


class SPYCC0DTE(QCAlgorithm):
    def Initialize(self):
        # Change to DEV=False before cloud push
        DEV: bool = False
        SELL_DELAY: int = 0  # Delay to sell CCs (in minutes)
        INITIAL_CASH: int = 1_000_000  # $USD

        if DEV:
            self.tkr = "TWX"
            self.SetStartDate(2014, 6, 4)
            self.SetEndDate(2014, 6, 7)
        else:
            self.tkr = "SPY"
            self.SetStartDate(2023, 1, 1)
            today = date.today()
            self.SetEndDate(today.year, today.month, today.day)

        self.SellDelay = timedelta(0, max(SELL_DELAY, 1) * 60)
        self.SetCash(INITIAL_CASH)
        self.SetBrokerageModel(
            BrokerageName.InteractiveBrokersBrokerage, AccountType.Cash
        )

        # No margin required because all calls should be covered...
        self.Settings.FreePortfolioValuePercentage = 1

        # Our benchmark
        self.underlying = self.AddEquity(self.tkr, Resolution.Minute).Symbol
        self.SetBenchmark(SecurityType.Equity, self.underlying)

        self.option = self.AddOption(self.tkr, Resolution.Minute)
        self.symbol = self.option.Symbol

        if DEV:
            self.option.SetFilter(self.devFilterOptions)
        else:
            self.option.SetFilter(self.filterOptions)

        # Used for plotting
        self.initial_price = None
        self.initial_cash = INITIAL_CASH

    def filterOptions(self, universe: OptionFilterUniverse) -> OptionFilterUniverse:
        return (
            universe.OnlyApplyFilterAtMarketOpen()
            .IncludeWeeklys()
            .CallsOnly()
            .Expiration(0, 0)
            .Strikes(1, 3)
        )

    def devFilterOptions(self, universe: OptionFilterUniverse) -> OptionFilterUniverse:
        return (
            universe.OnlyApplyFilterAtMarketOpen()
            .IncludeWeeklys()
            .CallsOnly()
            .Expiration(0, 100)
            .Strikes(0, 100)
        )

    def OnData(self, data: Slice):
        if not self.IsSellTime:
            return

        if self.underlying in data:
            buying_power = self.Portfolio.GetBuyingPower(self.underlying)
            purchase_volume = int((buying_power / data[self.underlying].Price) // 100)
            if purchase_volume > 0:
                self.Log(f"BUYING SPY: {purchase_volume * 100}")
                self.MarketOrder(self.underlying, purchase_volume * 100)

        if self.symbol in data.OptionChains:
            options = list(data.OptionChains[self.symbol])
            options.sort(key=lambda o: (o.Expiry, o.Strike))
            numCoverable = self.NumCoverable
            if numCoverable:
                covered = 0
                for option in options:
                    to_cover = numCoverable - covered
                    purchase_volume = int(min(to_cover, option.BidSize * 0.8))
                    self.Log(
                        f"SELLING CALL: {option.Strike} {option.Expiry.date()} {purchase_volume}"
                    )
                    self.MarketOrder(option.Symbol, -purchase_volume)
                    covered += purchase_volume
                    if covered >= numCoverable:
                        break

        self.Plotting(data)

    @property
    def IsSellTime(self) -> bool:
        diff = self.Time - self.Time.replace(hour=9, minute=30, second=0, microsecond=0)
        return diff == self.SellDelay

    @property
    def SoldCalls(self) -> List[OptionHolding]:
        return [
            holding
            for holding in map(lambda x: x.Value, self.Portfolio)
            if holding.Invested and holding.Type == SecurityType.Option
        ]

    @property
    def NumCoverable(self) -> int:
        capacity = self.Portfolio[self.underlying].Quantity // 100
        sold = sum(holding.Quantity for holding in self.SoldCalls)
        return int(capacity + sold)

    def Plotting(self, data: Slice):
        if self.initial_price is None:
            self.initial_price = data[self.underlying].Price

        bench_price = data[self.underlying].Price
        bench_performance = bench_price / self.initial_price

        current_value = self.Portfolio.TotalPortfolioValue
        current_performance = current_value / self.initial_cash

        ratio = current_performance / bench_performance

        self.Plot("VBENCHMARK", "BENCHMARK", bench_performance)
        self.Plot("VBENCHMARK", "PERFORMANCE", current_performance)
        self.Plot("VBENCHMARK", "RATIO", ratio)
