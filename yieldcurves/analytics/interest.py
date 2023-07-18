from math import prod

from ..compounding import compounding_factor, compounding_rate, \
    simple_rate, continuous_compounding, continuous_rate
from ..tools.adapter import CurveAdapter, init_curve
from ..tools import integrate, EPS

from .rate import CompoundingRate


class ShortRate(CurveAdapter):

    def __init__(self, curve, frequency=None, eps=None, *, invisible=None):
        """short curve from discount factor curve

        :param curve: discount factor curve
        :param frequency: compounding frequency
        :param eps:
        :param invisible: hide adapter in string representation

        hint to derive short rate (as instantanous forward rate) invoke same
        start and stop date

        >>> continuous = CompoundingRate(.02, frequency=None, invisible=True)
        >>> continuous(1.1, 1.1)
        0.2

        """
        super().__init__(init_curve(curve), invisible=invisible)
        self.frequency = frequency
        self.eps = eps
        self._eps = eps or EPS

    def __call__(self, x, y=None):
        """short rate from zero rate"""
        if x == y:
            y = x + self._eps
        if isinstance(self.curve, CompoundingRate):
            return self.curve(x, y)
        fx = continuous_compounding(self.curve(x), x)
        fy = continuous_compounding(self.curve(y), y)
        return continuous_rate(fy / fx, y - x)


class CompoundingShortRate(CurveAdapter):

    def __init__(self, curve, frequency=None, *, invisible=None):
        super().__init__(init_curve(curve), invisible=invisible)
        self.frequency = frequency

    def __call__(self, x, y=None):
        """zero rate from short rate"""
        if y is None:
            x, y = 0.0, x
        if x == y:
            return self.curve(x)
        r = integrate(self.curve, x, y)[0] / (y - x)
        # if self.frequency is not None:
        #     f = compounding_factor(r, y - x)
        #     r = compounding_rate(f, y - x, self.frequency)
        return r


class CashRate(CurveAdapter):

    def __init__(self, curve, frequency=None, invisible=None):
        super().__init__(init_curve(curve), invisible=invisible)
        self.frequency = frequency

    def __call__(self, x, y=None):
        if y is None:
            y = x + 1 / float(self.frequency)
        fx = compounding_factor(self.curve(x), x, self.frequency)
        fy = compounding_factor(self.curve(y), y, self.frequency)
        return simple_rate(fy / fx, y - x)


class CompoundingCashRate(CurveAdapter):

    def __init__(self, curve, frequency=None, *, invisible=None):
        super().__init__(init_curve(curve), invisible=invisible)
        self.frequency = frequency

    def __call__(self, x, y=None):
        """zero rate from cash rate"""
        if y is None:
            x, y = 0.0, x
        if x == y:
            return self.curve(x)
        if x > y:
            return -self(y, x)
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
