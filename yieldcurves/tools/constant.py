# -*- coding: utf-8 -*-

# yieldcurves
# -----------
# A Python library for financial yield curves.
#
# Author:   sonntagsgesicht
# Version:  0.2.2, copyright Thursday, 22 August 2024
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


class constant:
    """constant curve"""

    def __init__(self, curve):
        self.curve = float(curve)

    def __call__(self, x):
        return self.curve

    def __bool__(self):
        return bool(self.curve)

    def __float__(self):
        return self.curve

    def __str__(self):
        return str(self.curve)

    def __repr__(self):
        return repr(self.curve)

    def __eq__(self, other):
        if isinstance(other, constant):
            other = other.curve
        return self.curve == other

    def __neg__(self):
        return self.__class__(-self.curve)

    def __abs__(self):
        return self.__class__(abs(self.curve))

    def __add__(self, other):
        return self.__class__(self.curve + other)

    def __radd__(self, other):
        return other + self.curve

    def __sub__(self, other):
        return self.__class__(self.curve - other)

    def __rsub__(self, other):
        return other - self.curve

    def __mult__(self, other):
        return self.__class__(self.curve * other)

    def __rmult__(self, other):
        return other * self.curve

    def __truediv__(self, other):
        return self.__class__(self.curve / other)

    def __rtruediv__(self, other):
        return other / self.curve

    def __floordiv__(self, other):
        return self.__class__(self.curve // other)

    def __rfloordiv__(self, other):
        return other // self.curve

    def __mod__(self, other):
        return self.__class__(self.curve % other)

    def __rmod__(self, other):
        return other % self.curve


def init(curve):
    if callable(curve):
        return curve
    if not isinstance(curve, (float, int)):
        cls = curve.__class__.__qualname__
        msg = f"float or callable required but type {cls} given"
        raise TypeError(msg)
    return constant(curve)
