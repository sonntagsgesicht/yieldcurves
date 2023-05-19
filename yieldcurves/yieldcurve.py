
from .repr import representation

from .assetprice import price_price, price_yield, forward_price
from .interestrate import zero_rate, cash_rate, short_rate, zero_rate_df, \
    cash_rate_df, short_rate_df
from .creditprobability import probability_prob, pd, pd_prob, marginal, \
    marginal_prob, intensity, intensity_prob, hazard_rate, hazard_rate_prob
from .volatility import vol, terminal_vol, instantaneous_vol

from .curve import init_curve, curve_algebra


class base_curve:

    __slots__ = 'curve', '_kwargs'

    def __init__(self, curve, **kwargs):
        self.curve = init_curve(curve)
        self._kwargs = kwargs

    def __str__(self):
        return representation(self, self.curve, **self._kwargs, rstyle=False)

    def __repr__(self):
        return representation(self, self.curve, **self._kwargs)

    def __getattr__(self, item):
        if item in self._kwargs:
            return self._kwargs[item]
        return super().__getattribute__(item)

    def __getitem__(self, item):
        return self.curve[item]

    def __setitem__(self, key, value):
        self.curve[key] = value

    def __delitem__(self, key):
        del self.curve[key]

    def __iter__(self):
        return iter(self.curve)

    def __contains__(self, item):
        return item in self.curve


# --- price curve classes ---


class base_price_curve(base_curve):
    __slots__ = 'curve', '_kwargs'

    def __init__(self, curve, spot=1.0):
        super().__init__(curve, spot=spot)

    def price(self, x):
        raise NotImplementedError()

    def yields(self, x):
        return price_yield(self.price, x)


class price_curve(base_price_curve):
    """forward price from spot price and yield curve"""

    def __call__(self, x):
        return self.price(x)

    def price(self, x):
        return forward_price(self.curve, self.spot, x)


class yield_curve(base_price_curve):
    """price yield from price curve"""

    def __call__(self, x):
        return self.yields(x)

    def price(self, x):
        return price_price(self.curve, self.spot, x)


class fx_curve(base_price_curve):
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
        return forward_price(self.curve, self.spot, x)


# --- credit probability curve classes ---


class base_probability_curve(base_curve):
    __slots__ = 'curve', '_kwargs'

    def prob(self, x):
        raise NotImplementedError()

    def pd(self, x):
        return pd(self.curve, x)

    def marginal(self, x):
        return marginal(self.curve, x)

    def intensity(self, x):
        return intensity(self.curve, x)

    def hazard_rate(self, x):
        return hazard_rate(self.curve, x)


class survival_probability_curve(base_probability_curve):

    def __call__(self, x):
        return self.prob(x)

    def prob(self, x):
        return probability_prob(self.curve, x)


class default_probability_curve(base_probability_curve):

    def __call__(self, x):
        return self.pd(x)

    def prob(self, x):
        return pd_prob(self.curve, x)


class marginal_survival_probability_curve(base_probability_curve):

    def __call__(self, x):
        return self.marginal(x)

    def prob(self, x):
        return marginal_prob(self.curve, x)


class intensity_probability_curve(base_probability_curve):

    def __call__(self, x):
        return self.intensity(x)

    def prob(self, x):
        return intensity_prob(self.curve, x)


class hazard_rate_probability_curve(base_probability_curve):

    def __call__(self, x):
        return self.hazard_rate(x)

    def prob(self, x):
        return hazard_rate_prob(self.curve, x)


# --- interest rate curve classes ---


class base_rate_curve(base_curve):
    __slots__ = 'curve', '_kwargs'

    def __init__(self, curve, compounding_frequency=None):
        super().__init__(curve, compounding_frequency=compounding_frequency)

    def df(self, x, y=0.0):
        raise NotImplementedError()

    def rate(self, x):
        return zero_rate(self.df, x)

    def cash(self, x):
        return cash_rate(self.df, x)

    def short(self, x):
        return short_rate(self.df, x)


class zero_rate_curve(base_rate_curve):

    def __call__(self, x):
        return self.rate(x)

    def df(self, x, y=0.0):
        return zero_rate_df(self.curve, x, y, self.compounding_frequency)


class cash_rate_curve(base_rate_curve):

    def __call__(self, x):
        return self.cash(x)

    def df(self, x, y=0.0):
        return cash_rate_df(self.curve, x, y, self.compounding_frequency)


class short_Rate_curve(base_rate_curve):

    def __call__(self, x):
        return self.short(x)

    def df(self, x, y=0.0):
        return short_rate_df(self.curve, x, y, self.compounding_frequency)


# --- volatility curve classes ---


class base_volatility_curve(base_curve):
    __slots__ = 'curve', '_kwargs'

    def vol(self, x):
        raise NotImplementedError()

    def instantaneous(self, x):
        return instantaneous_vol(self.vol, x)


class instantaneous_volatility_curve(base_volatility_curve):

    def __call__(self, x):
        return self.instantaneous(x)

    def vol(self, x):
        return terminal_vol(self.curve, x)


class terminal_volatility_curve(base_volatility_curve):

    def __call__(self, x):
        return self.vol(x)

    def vol(self, x):
        return vol(self.curve, x)
