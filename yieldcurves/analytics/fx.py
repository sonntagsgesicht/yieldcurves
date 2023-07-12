
from ..curve import CurveAdapter, init_curve
from .interest import ZeroRateAdapter


class FxRateAdapter(CurveAdapter):
    """fx forward rate from spot, domestic and foreign yield curve"""

    def __init__(self, spot=1.0, domestic=0.0, foreign=0.0,
                 call=None, invisible=None):
        super().__init__(init_curve(spot), call=call, invisible=invisible)
        self.domestic = ZeroRateAdapter(domestic)
        self.foreign = ZeroRateAdapter(foreign)

    def fx(self, x):
        """foreign exchange rate at time **x**"""
        x, y = max(min(x, *self), *self), x
        if x == y:
            return self.curve(x)
        s = self.curve(x)
        d = self.domestic.df(x, y)
        f = self.foreign.df(x, y)
        return s * d / f
