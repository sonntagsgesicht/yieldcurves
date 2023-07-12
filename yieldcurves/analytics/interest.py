from math import prod

from ..compounding import compounding_factor, compounding_rate, \
    simple_rate, continuous_compounding, continuous_rate
from ..curve import CurveAdapter, init_curve
from ..tools import integrate

EPS = 1 / 250


class ZeroRateAdapter(CurveAdapter):

    def __init__(self, curve, frequency=None, call=None, invisible=None):
        super().__init__(init_curve(curve), call=call, invisible=invisible)
        self.frequency = frequency

    def zero(self, x, y=None):
        if y is None:
            # x, y = 0.0, x
            return self.curve(x)
        if x == y:
            return self.zero(x, x + EPS)
        fx = compounding_factor(self.curve(x), x, self.frequency)
        fy = compounding_factor(self.curve(y), y, self.frequency)
        return compounding_rate(fy / fx, y - x, frequency=self.frequency)

    def df(self, x, y=None):
        if y is None:
            return compounding_factor(self.zero(x), x, self.frequency)
        if x == y:
            return 1.0
        return self.df(y) / self.df(x)

    def short(self, x, y=None):
        if y is None:
            y = x + EPS
        fx = continuous_compounding(self.zero(x), x)
        fy = continuous_compounding(self.zero(y), y)
        return continuous_rate(fy / fx, y - x)

    def cash(self, x, y=None):
        if y is None:
            y = x + 1 / self.frequency
        fx = compounding_factor(self.zero(x), x, self.frequency)
        fy = compounding_factor(self.zero(y), y, self.frequency)
        return simple_rate(fy / fx, y - x)


class DiscountFactorAdapter(ZeroRateAdapter):

    def zero(self, x, y=None):
        if y is None:
            x, y = 0.0, x
        if x == y:
            y = x + EPS
        f = self.curve(y) / self.curve(x)
        return compounding_rate(f, y - x, self.frequency)


class ShortRateAdapter(ZeroRateAdapter):

    def zero(self, x, y=None):
        if y is None:
            x, y = 0.0, x
        if x == y:
            return self.curve(x)
        r = integrate(self.curve, x, y)[0] / (y - x)
        # todo: convert compounding
        # f = compounding_factor(r, y - x)
        # r = compounding_rate(f, y - x, self.frequency)
        return r

    def short(self, x, y=None):
        return self.curve(x)


class CashRateAdapter(ZeroRateAdapter):

    def zero(self, x, y=None):
        if y is None:
            x, y = 0.0, x
        if x == y:
            return self.curve(x)
        if x > y:
            return -self.zero(y, x)
        if not self.frequency:
            return self.curve(x)

        # df from compound forward rates
        # integrate from x to y the discount factor f
        n = 0
        tenor = 1 / self.frequency
        while x + (n + 1) * tenor < y:
            n += 1
        frequency = 0
        f = prod(compounding_factor(self.curve(x + i * tenor),
                                    tenor, frequency) for i in range(n))
        e = x + n * tenor
        f *= compounding_factor(self.curve(e), y - e, frequency)
        return compounding_rate(f, y - x, frequency=self.frequency)

    def cash(self, x, y=None):
        if y is None or not self.frequency or y == x + 1 / self.frequency:
            return self.curve(x)
        fx = compounding_factor(self.zero(x), x, self.frequency)
        fy = compounding_factor(self.zero(y), y, self.frequency)
        return simple_rate(fy / fx, y - x)
