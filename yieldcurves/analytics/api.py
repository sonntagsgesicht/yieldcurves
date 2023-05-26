
from ..curve import curve_wrapper, init_curve, curve_algebra

from . import assetprice as _price
from . import creditprobability as _prob
from . import interestrate as _rate
from . import volatility as _vol


class price_curve(curve_wrapper):
    """price yield from price curve"""

    def __init__(self, curve, spot=1.0):
        spot = init_curve(spot)
        curve = init_curve(curve)
        super().__init__(curve, spot=spot)

    def price(self, x):
        return _price.forward_price(self.curve, self.spot, x)

    def price_yield(self, x):
        return _price.price_yield(self.price, x)


class yield_curve(price_curve):
    """price yield from price curve"""

    def price(self, x):
        return _price.price_price(self.curve, self.spot, x)


class fx_curve(price_curve):
    """forward fx rate from spot rate as well
    domestic and foreign interest rate curve"""

    def __init__(self, spot, domestic=0.0, foreign=0.0):
        domestic = init_curve(domestic)
        foreign = init_curve(foreign)
        curve = curve_algebra(domestic) / foreign
        super().__init__(curve, spot)

    def __call__(self, x):
        return self.price(x)

    def price(self, x):
        return _price.forward_price(self.curve, self.spot, x)


class prob_curve(curve_wrapper):

    def __init__(self, curve):
        curve = init_curve(curve)
        super().__init__(curve)

    def prob(self, x):
        return _prob.probability_prob(self.curve, x)

    def pd(self, x):
        return _prob.pd(self.prob, x)

    def marginal(self, x):
        return _prob.marginal(self.prob, x)

    def intensity(self, x):
        return _prob.intensity(self.prob, x)

    def hazard_rate(self, x):
        return _prob.hazard_rate(self.prob, x)


class rate_curve(curve_wrapper):

    def __init__(self, curve, frequency=None, df=None):
        self._df = df or _rate.zero_rate_df
        curve = init_curve(curve)
        super().__init__(curve, frequency=frequency)

    def df(self, x, y=0.0):
        return self._df(self.curve, x, y, frequency=self.frequency)

    def rate(self, x, y=0.0):
        return self.zero(x, y)

    def zero(self, x, y=0.0):
        return _rate.zero_rate(self.df, x, y, frequency=self.frequency)

    def cash(self, x, y=0.0):
        y = x + 1 / self.frequency if y is None else y
        return _rate.cash_rate(self.df, y, x)

    def short(self, x):
        return _rate.short_rate(self.df, x)


class vol_curve(curve_wrapper):

    def __init__(self, curve):
        curve = init_curve(curve)
        super().__init__(curve)

    def vol(self, x):
        return _vol.vol(self.curve, x)

    def instantaneous(self, x):
        return _vol.instantaneous_vol(self.vol, x)

    def terminal(self, x):
        return self.vol(x)


# --- price curve classes ---


class price(price_curve):
    """forward price from spot price and yield curve"""

    pass


class price_yield(price_curve):
    """price yield from price curve"""

    def price(self, x):
        return _price.price_price(self.curve, self.spot, x)


class fx(price):
    """forward fx rate from spot rate as well
    domestic and foreign interest rate curve"""

    def __init__(self, spot, domestic=0.0, foreign=0.0):
        domestic = init_curve(domestic)
        foreign = init_curve(foreign)
        curve = curve_algebra(domestic) / foreign
        super().__init__(curve, spot)

    def __call__(self, x):
        return self.price(x)

    def price(self, x):
        return _price.forward_price(self.curve, self.spot, x)


# --- credit probability curve classes ---


class prob(prob_curve):

    pass


class pd(prob_curve):

    def prob(self, x):
        return _prob.pd_prob(self.curve, x)


class marginal(prob_curve):

    def prob(self, x):
        return _prob.marginal_prob(self.curve, x)


class intensity(prob_curve):

    def prob(self, x):
        return _prob.intensity_prob(self.curve, x)


class hazard_rate(prob_curve):

    def prob(self, x):
        return _prob.hazard_rate_prob(self.curve, x)


# --- interest rate curve classes ---


class zero(rate_curve):

    pass


class cash(rate_curve):

    def df(self, x, y=0.0):
        return _rate.cash_rate_df(self.curve, x, y, frequency=self.frequency)


class short(rate_curve):

    def df(self, x, y=0.0):
        return _rate.short_rate_df(self.curve, x, y, frequency=self.frequency)


# --- volatility curve classes ---


class terminal(vol_curve):

    pass


class instantaneous(vol_curve):

    def vol(self, x):
        return _vol.terminal_vol(self.curve, x)
