from math import prod
from scipy.integrate import quad as integrate

from ..compounding import compounding_factor, compounding_rate, \
    simple_rate, continuous_compounding, continuous_rate
from ..curve import CurveAdapter, init_curve

EPS = 1 / 250


# short -> zero (<-> df) -> cash

class Cv(CurveAdapter):
    """curve from curve to add call signature"""

    def __init__(self, curve, frequency=None):
        super().__init__(init_curve(curve), invisible=True)
        self.frequency = frequency or getattr(curve, 'frequency', None)

    def __call__(self, x, y=None):
        if y is not None:
            raise NotImplementedError()
        return self.curve(x)


class DfZ(CurveAdapter):
    """discount factors from zero rate curve"""

    def __init__(self, curve, frequency=None):
        super().__init__(init_curve(curve))
        self.frequency = frequency or getattr(curve, 'frequency', None)

    def __call__(self, x, y=None):
        if y is None:
            return compounding_factor(self.curve(x), x, self.frequency)
        if x == y:
            return 1.0
        return self(y) / self(x)


Df = DfZ


class ZeroDf(CurveAdapter):
    """zero rates from discount factor curve"""

    def __init__(self, curve, frequency=None):
        super().__init__(init_curve(curve))
        self.frequency = frequency or getattr(curve, 'frequency', None)

    def __call__(self, x, y=None):
        if y is None:
            x, y = 0.0, x
        if x == y:
            y = x + EPS
        f = self.curve(y) / self.curve(x)
        return continuous_rate(f, y - x)


Zero = ZeroDf


class ZeroZ(Zero):
    """zero rates from zero rate curve"""

    def __call__(self, x, y=None):
        if y is None:
            x, y = 0.0, x
        if x == y:
            return self(x, x + EPS)
        fx = compounding_factor(self.curve(x), x, self.frequency)
        fy = compounding_factor(self.curve(y), y, self.frequency)
        return compounding_rate(fy / fx, y - x, frequency=self.frequency)


class ZeroS(Zero):
    """zero rates from short rate curve"""

    def __call__(self, x, y=None):
        if y is None:
            x, y = 0.0, x
        if x == y:
            return self.curve(x)
        return integrate(self.curve, x, y)[0] / (y - x)


class ZeroC(Zero):
    """zero rates from cash rate curve"""

    def __call__(self, x, y=None):
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


class ShortZ(CurveAdapter):
    """(forward) short rates from zero rate curve"""

    def __init__(self, curve):
        super().__init__(init_curve(curve))

    def __call__(self, x, y=None):
        if y is None:
            y = x + EPS
        fx = continuous_compounding(self.curve(x), x)
        fy = continuous_compounding(self.curve(y), y)
        return continuous_rate(fy / fx, y - x)


Short = ShortZ


class CashZ(CurveAdapter):
    """cash rates from zero rate curve"""

    def __init__(self, curve, frequency=None):
        super().__init__(init_curve(curve))
        self.frequency = frequency or getattr(curve, 'frequency', None)

    def __call__(self, x, y=None):
        if y is None:
            y = x + 1 / self.frequency
        fx = compounding_factor(self.curve(x), x, self.frequency)
        fy = compounding_factor(self.curve(y), y, self.frequency)
        return simple_rate(fy / fx, y - x)


Cash = CashZ


class CashC(Cash):
    """cash rates from cash rate curve"""

    def __init__(self, curve, frequency=None):
        super().__init__(ZeroC(curve, frequency=frequency))
        self.frequency = frequency or getattr(curve, 'frequency', None)

    def __call__(self, x, y=None):
        if y is None or \
                not self.frequency or y == x + 1 / self.frequency:
            return self.curve.curve(x)
        return super().__call__(x, y)


'''
CashRate(ZeroRateCurve(curve))(x)
ZeroRate(ShortRateCurve(curve))(x)
'''
