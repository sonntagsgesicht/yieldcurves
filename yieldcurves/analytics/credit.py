from math import prod
from ..compounding import continuous_compounding, continuous_rate
from ..curve import curve_wrapper, init_curve
from .rate import compounding_forwards, EPS


def probability_prob(curve, x, y=0.0):
    """survival probability from probability of default (pd)"""
    return curve(x) / curve(y)


def pd(prob, x):
    """probability of default (pd) from survival probability"""
    return 1. - prob(x)


def pd_prob(curve, x):
    """survival probability from probability of default (pd)"""
    return 1. - curve(x)


def marginal(prob, x):
    """marginal survival probability from survival probability"""
    return prob(x + 1) / prob(x)


def marginal_prob(curve, x):
    """survival probability from marginal survival probability"""
    grid = list(float(i) for i in range(int(x))) + [x]
    return prod(curve(g) for g in grid)


def intensity(prob, x):
    """intensity from survival probability"""
    return continuous_rate(prob(x), x)


def intensity_prob(curve, x):
    """survival probability from intensity"""
    return continuous_compounding(curve(x), x)


def hazard_rate(prob, x):
    """hazard_rate from survival probability"""
    rx = intensity(prob, x)
    ry = intensity(prob, x + EPS)
    return (rx - ry) / EPS


def hazard_rate_prob(curve, x):
    """survival probability from hazard rate"""
    return compounding_forwards(curve, x)


# --- credit probability curve classes ---

class credit_curve(curve_wrapper):

    def __init__(self, curve, curve_type='prob'):
        if curve_type in 'probability_curve' or curve_type in 'credit_curve':
            self._prob = probability_prob
        elif curve_type in 'pd_curve' or curve_type in 'default_curve':
            self._prob = pd_prob
        elif curve_type in 'marginal_curve':
            self._prob = marginal_prob
        elif curve_type in 'intensity_curve':
            self._prob = intensity_prob
        elif curve_type in 'hazard_rate_curve' or curve_type in 'hz_curve':
            self._prob = hazard_rate_prob
        else:
            raise TypeError(f'no credit curve of type {curve_type}')

        curve = init_curve(curve)
        super().__init__(curve)

    def prob(self, x):
        return self._prob(self.curve, x)

    def pd(self, x):
        return pd(self.prob, x)

    def marginal(self, x):
        return marginal(self.prob, x)

    def intensity(self, x):
        return intensity(self.prob, x)

    def hazard_rate(self, x):
        return hazard_rate(self.prob, x)
