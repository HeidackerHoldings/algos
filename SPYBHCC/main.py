from AlgorithmImports import *
from datetime import datetime, timedelta


class SPYBHCC(QCAlgorithm):
    def Initialize(self):
        t = datetime.today()
        i = t - timedelta(365 * 20)
        self.SetStartDate(i.year, i.month, i.day)
        self.SetEndDate(t.year, t.month, t.day)
        self.SetCash(100000)
        self.symbol = self.AddEquity("SPY", Resolution.Minute).Symbol

    def OnData(self, data: Slice):
        if not self.Portfolio.Invested:
            self.SetHoldings(self.symbol, 1)
            self.Debug("Purchased Stock")
