# -*- coding: utf-8 -*-

# yieldcurves
# -----------
# A Python library for financial yield curves.
#
# Author:   sonntagsgesicht
# Version:  0.2.1, copyright Tuesday, 16 July 2024
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


class ConstantCurve:
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
        if isinstance(other, ConstantCurve):
            other = other.curve
        return self.curve == other


def init(curve):
    if callable(curve):
        return curve
    if not isinstance(curve, (float, int)):
        cls = curve.__class__.__qualname__
        msg = f"float or callable required but type {cls} given"
        raise TypeError(msg)
    return ConstantCurve(curve)
