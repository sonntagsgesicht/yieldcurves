# -*- coding: utf-8 -*-

# yieldcurves
# -----------
# A Python library for financial yield curves.
#
# Author:   sonntagsgesicht
# Version:  0.1, copyright Saturday, 22 April 2023
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


from re import compile as _compile
from scipy.integrate import quad as _integrate  # noqa F401
from .ap3 import plot as ascii_plot  # noqa F401
from .mpl import plot, lin  # noqa F401
from .algebra import AlgebraCurve  # noqa F401

EPS = 1 / 365.25
ITERABLE = list, tuple

# integrate = (lambda c, x, y: _integrate(c, float(x), float(y)))
integrate = _integrate

_p1 = _compile(r'(.)([A-Z][a-z]+)')
_p2 = _compile(r'([a-z0-9])([A-Z])')


def snake_case(name):
    """convert camel case to snake case"""
    return _p2.sub(r'\1_\2', _p1.sub(r'\1_\2', name)).lower()
