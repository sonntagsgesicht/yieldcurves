
from ..compounding import continuous_compounding, continuous_rate
from ..curve import CurveAdapter, init_curve
from .rate import Df


# yield <-> price

class Price(CurveAdapter):
    """price from yield curve"""

    def __init__(self, curve, spot=1.0):
        super().__init__(init_curve(curve))
        self.spot = init_curve(spot)

    def __call__(self, x, y=None):
        if y is None:
            x, y = 0.0, x
        s = self.spot(x)
        d = continuous_compounding(self.curve(x), x)
        f = continuous_compounding(self.curve(y), y)
        return s * f / d


class Yield(CurveAdapter):
    """yield from price curve"""

    def __init__(self, curve):
        super().__init__(init_curve(curve))

    def __call__(self, x, y=None):
        if y is None:
            x, y = 0.0, x
        f = self.curve(y) / self.curve(x)
        return continuous_rate(f, y - x)


class Fx(CurveAdapter):
    """fx forward rate from spot, domestic and foreign yield curve"""

    def __init__(self, spot=1.0, domestic=0.0, foreign=0.0):
        super().__init__(init_curve(spot))
        self.domestic = Df(domestic)
        self.foreign = Df(foreign)

    def __call__(self, x, y=None):
        if y in None:
            x, y = 0.0, x
        s = self.curve(x)
        d = self.domestic(x, y)
        f = self.foreign(x, y)
        return s * d / f
