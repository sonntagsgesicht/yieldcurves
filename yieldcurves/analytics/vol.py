
from ..curve import curve_wrapper, init_curve

from .rate import EPS


def vol(curve, x):
    """terminal volatility from instantaneous volatility"""
    return curve(x)


def terminal_vol(curve, x):
    """terminal volatility from instantaneous volatility"""
    return curve(x)


def instantaneous_vol(curve, x):
    """instantaneous volatility from terminal volatility"""
    return curve(x + EPS) - curve(x)


# --- volatility curve classes ---

class vol_curve(curve_wrapper):

    def __init__(self, curve, curve_type='terminal'):
        curve = init_curve(curve)
        if curve_type in 'terminal_vol':
            self._vol = vol
        if curve_type in 'instantaneous_vol':
            self._vol = terminal_vol
        else:
            raise TypeError(f'no vol curve of type {curve_type}')
        super().__init__(curve)

    def vol(self, x):
        return self._vol(self.curve, x)

    def instantaneous(self, x):
        return instantaneous_vol(self.vol, x)

    def terminal(self, x):
        return self.vol(x)
