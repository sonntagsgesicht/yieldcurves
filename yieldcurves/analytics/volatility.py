
from .interestrate import EPS


def vol(curve, x):
    """terminal volatility from instantaneous volatility"""
    return curve(x)


def terminal_vol(curve, x):
    """terminal volatility from instantaneous volatility"""
    return curve(x)


def instantaneous_vol(curve, x):
    """instantaneous volatility from terminal volatility"""
    return curve(x + EPS) - curve(x)
