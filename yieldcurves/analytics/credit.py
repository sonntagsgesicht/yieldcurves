from math import prod
from ..tools.adapter import CurveAdapter
from ..compounding import compounding_factor, compounding_rate


class MarginalProb(CurveAdapter):

    def __call__(self, x):
        """marginal prob from prob"""
        return self.curve(x, x + 1.0)


class CompoundingMarginalProb(CurveAdapter):

    def __call__(self, x, y=None):
        """prob from marginal prob"""
        if y is None:
            x, y = 0.0, x
        if x == y:
            return self.curve(x)
        if x > y:
            return -self(y, x)

        # prob from compound marginal prob
        n = 0
        step = 1.
        while x + (n + 1) * step < y:
            n += 1
        f = prod(self.curve(x + i * step) for i in range(n))
        e = x + n * step
        r = compounding_rate(self.curve(e), step)
        return f * compounding_factor(r, y - e)


class DefaultProb(CurveAdapter):

    def __call__(self, x, y=None):
        """default prob from prob and visa versa"""
        if y is None:
            return 1. - self.curve(x)
        if isinstance(self.curve, CurveAdapter):
            return 1. - self.curve(x, y)
        return 1. - self.curve(y) / self.curve(x)
