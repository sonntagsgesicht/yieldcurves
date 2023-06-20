from ..compounding import continuous_compounding, continuous_rate
from ..curve import CurveAdapter, init_curve
from .rate import Zero, Short, ZeroS, ZeroZ, Df


# hz -> intensity <-> prob -> pd / marginal

HazardRate = type('HazardRate', (Short,),
                  {'__doc__': """hazard rate from intensity curve"""})
Intensity = type('Intensity', (Zero,),
                 {'__doc__': """intensity from probability curve"""})
IntensityHz = type('IntensityHz', (ZeroS,),
                   {'__doc__': """intensity from hazard rate curve"""})
IntensityI = type('IntensityI', (ZeroZ,),
                  {'__doc__': """intensity from intensity curve"""})
Prob = type('Prob', (Df,),
            {'__doc__': """survival probability from intensity curve"""})


class Pd(CurveAdapter):
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


class Marginal(CurveAdapter):
    """marginal (forward) probability from survival probability curve"""

    def __init__(self, curve):
        super().__init__(init_curve(curve))

    def __call__(self, x, y=None):
        if y is None:
            y = x + 1
        if x == y:
            return 1.0
        return self.curve(y) / self.curve(x)


class ProbM(Prob):
    """survival probability from marginal (forward) probability curve"""

    def __call__(self, x, y=None):
        if y is None:
            x, y = 0.0, x
        if x == y:
            return 1.0
        f = t = 1.0
        while x + t < y:
            f *= self.curve(x)
            x += t
        r = continuous_rate(self.curve(x), t)
        f *= continuous_compounding(r, y - x)
        return f
