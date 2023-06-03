from math import prod

from ..curve import CurveWrapper, init_curve
from ..compounding import compounding_factor, compounding_rate, \
    simple_rate, simple_compounding, continuous_compounding, continuous_rate

EPS = 1e-7

# short -> zero -> df / cash
# hz -> intensity -> prob -> pd / marginal
# yield -> price
# inst vol -> terminal vol


def compounding_df(curve, x, y, tenor=None):
    """compound forward rates"""
    # integrate from y to x the discount factor f
    if x == y:
        return 1.0
    if x < y:
        return 1 / compounding_df(curve, y, x, tenor=tenor)
    compounding = simple_compounding if tenor else continuous_compounding
    t = tenor or EPS
    f = 1.0
    while x + t < y:
        f *= compounding(curve(x), t)
        x += t
    f *= compounding(curve(y), y - x)
    return f


class Cv(CurveWrapper):

    def __init__(self, curve):
        super().__init__(init_curve(curve), invisible=True)

    def __call__(self, x, y=None):
        if y is not None:
            raise NotImplemented()
        return self.curve(x)


class Df(CurveWrapper):
    """discount factors from zero rate curve"""

    def __init__(self, curve, frequency=None):
        super().__init__(init_curve(curve))
        self.frequency = frequency

    def __call__(self, x, y=None):
        if y is None:
            return compounding_factor(self.curve(x), x, self.frequency)
        if x == y:
            return 1.0
        return self(y) / self(x)


class Zero(CurveWrapper):
    """zero rates from discount factor curve"""

    def __init__(self, curve, frequency=None):
        super().__init__(init_curve(curve))
        self.frequency = frequency

    def __call__(self, x, y=None):
        if y is None:
            x, y = 0.0, x
        if x == y:
            return self(x, x + EPS)
        f = self.curve(y) / self.curve(x)
        return continuous_rate(f, y - x)


class ZeroZ(Zero):
    """zero rates from zero rate curve"""

    def __call__(self, x, y=None):
        if y is None:
            x, y = 0.0, x
        if x == y:
            return self(x, x + EPS)
        fx = compounding_factor(self.curve(x), x)
        fy = compounding_factor(self.curve(y), y)
        return compounding_rate(fy / fx, y - x, frequency=self.frequency)


class ZeroS(Zero):
    """zero rates from short rate curve"""

    def __call__(self, x, y=None):
        if y is None:
            x, y = 0.0, x
        if x == y:
            return self.curve(x)
        f = compounding_df(self.curve, x, y)
        return continuous_rate(f, y - x)


class ZeroC(Zero):
    """zero rates from cash rate curve"""

    def __call__(self, x, y=None):
        if y is None:
            x, y = 0.0, x
        if x == y:
            return self.curve(x)
        t = 1 / self.frequency if self.frequency else y - x
        f = compounding_df(self.curve, x, y, tenor=t)
        return compounding_rate(f, y - x, frequency=self.frequency)


class Short(CurveWrapper):
    """short rates from zero rate curve"""

    def __init__(self, curve):
        super().__init__(init_curve(curve))

    def __call__(self, x, y=None):
        if y is None:
            y = x + EPS
        fx = continuous_compounding(self.curve(x), x)
        fy = continuous_compounding(self.curve(y), y)
        return continuous_rate(fy / fx, y - x)


class Cash(CurveWrapper):
    """cash rates from zero rate curve"""

    def __init__(self, curve, frequency=None, tenor=None):
        super().__init__(init_curve(curve))
        self.frequency = frequency
        self.tenor = tenor

    def __call__(self, x, y=None):
        if y is None:
            t = 1 / self.frequency if self.frequency else 1 / 4
            t = self.tenor or t
            y = x + t
        fx = compounding_factor(self.curve(x), x, self.frequency)
        fy = compounding_factor(self.curve(y), y, self.frequency)
        return simple_rate(fy / fx, y - x)


class CashC(Cash):
    """cash rates from cash rate curve"""

    def __call__(self, x, y=None):
        if y is None:
            return self.curve(x)
        t = 1 / self.frequency if self.frequency else y - x
        f = compounding_df(self.curve, x, y, tenor=t)
        return simple_rate(f, y - x)


HazardRate = type('HazardRate', (Short,),
                  {'__doc__': """hazard rate from intensity curve"""})
Intensity = type('Intensity', (Zero,),
                 {'__doc__': """intensity from probability curve"""})
IntensityHz = type('IntensityHz', (ZeroS,),
                   {'__doc__': """intensity from hazard rate curve"""})
IntensityI = type('IntensityI', (ZeroS,),
                  {'__doc__': """intensity from intensity curve"""})


class Prob(CurveWrapper):
    """survival probability from intensity curve"""

    def __init__(self, curve):
        super().__init__(init_curve(curve))

    def __call__(self, x, y=None):
        if y is None:
            return continuous_compounding(self.curve(x), x)
        if x == y:
            return 1.0
        return self(y) / self(x)


class Pd(CurveWrapper):
    """default probability from survival probability curve"""

    def __init__(self, curve):
        super().__init__(init_curve(curve))

    def __call__(self, x, y=None):
        if y is None:
            return 1. - self.curve(x)
        return 1. - self.curve(y) / self.curve(x)


class ProbPd(Prob):
    """survival probability from default probability curve"""

    def __call__(self, x, y=None):
        if y is None:
            return 1. - self.curve(x)
        return self(y) / self(x)


class Marginal(CurveWrapper):
    """marginal (forward) probability from survival probability curve"""

    def __init__(self, curve):
        super().__init__(init_curve(curve))

    def __call__(self, x, y=None):
        if y is None:
            y = x + 1
        return self.curve(y) / self.curve(x)


class ProbM(Prob):
    """survival probability from marginal (forward) probability curve"""

    def __call__(self, x, y=None):
        if y is None:
            x, y = 0.0, x
        f = t = 1.0
        while x + t < y:
            f *= self.curve(x)
            x += t
        r = continuous_rate(self.curve(x), t)
        f *= continuous_compounding(r, y - x)
        return f


class Price(CurveWrapper):
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


class Yield(CurveWrapper):
    """yield from price curve"""

    def __init__(self, curve):
        super().__init__(init_curve(curve))

    def __call__(self, x, y=None):
        if y is None:
            x, y = 0.0, x
        f = self.curve(y) / self.curve(x)
        return continuous_rate(f, y - x)


class Fx(CurveWrapper):
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


class Terminal(CurveWrapper):
    """terminal vol from instantaneous vol curve"""

    def __init__(self, curve):
        super().__init__(init_curve(curve))

    def __call__(self, x, y=None):
        raise NotImplemented()
