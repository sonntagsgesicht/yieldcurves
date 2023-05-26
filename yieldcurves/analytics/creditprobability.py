from math import prod
from .compounding import continuous_compounding, continuous_rate

from .interestrate import compounding_forwards, EPS


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
