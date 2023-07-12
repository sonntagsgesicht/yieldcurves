from .obsolete.rate import *

from ..compounding import compounding_factor, compounding_rate, \
    simple_rate, continuous_compounding, continuous_rate
from ..curve import CurveAdapter, init_curve
from ..tools import integrate

EPS = 1 / 250


# --- RateAdapter ---

# short [diff(rate)] <-> rate [int(short)]
# rate [ln(price)/time] <-> price [exp(rate*time)]


class ContinuousRate(CurveAdapter):

    def __init__(self, curve, frequency=None, **__):
        super().__init__(curve, **__)
        self.frequency = frequency

    def __call__(self, x, y=None):
        x, y = self._pre(x), self._pre(y)
        fx = compounding_factor(self.curve(x), x, self.frequency)
        if y is None:
            return compounding_rate(fx, x)
        fy = compounding_factor(self.curve(y), y, self.frequency)
        return compounding_rate(fy / fx, y - x)


class RateAdapter(CurveAdapter):

    def __init__(self, curve, frequency=None, call=None, invisible=None):
        super().__init__(init_curve(curve), call=call, invisible=invisible)
        self.frequency = frequency

    def factor(self, x, y=None, frequency=None):
        x, y = self._pre(x), self._pre(y)
        if x == y:
            return 1.0
        fx = compounding_factor(self.curve(x), x, frequency)
        if y is None:
            return fx
        fy = compounding_factor(self.curve(y), y, frequency)
        return fy / fx

    def rate(self, x, y=None, frequency=None):
        x, y = self._pre(x), self._pre(y)
        if y is None:
            # x, y = 0.0, x
            return self.curve(x)
        if x == y:
            y = x + EPS
        fx = compounding_factor(self.curve(x), x, frequency)
        fy = compounding_factor(self.curve(y), y, frequency)
        return compounding_rate(fy / fx, y - x, frequency=frequency)
