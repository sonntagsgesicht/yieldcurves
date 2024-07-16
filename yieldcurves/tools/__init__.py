# -*- coding: utf-8 -*-

# yieldcurves
# -----------
# A Python library for financial yield curves.
#
# Author:   sonntagsgesicht
# Version:  0.2, copyright Monday, 01 July 2024
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


from re import compile as _compile
try:
    from scipy.integrate import quad as integrate  # noqa F401
except ImportError:
    def integrate(*args, **kwargs):
        raise ImportError("failed to import 'integrate' from 'scipy'")
from .ap3 import plot as ascii_plot  # noqa F401
from .mpl import plot, lin  # noqa F401
from .algebra import AlgebraCurve  # noqa F401

EPS = 1 / 365.25
ITERABLE = list, tuple


_p1 = _compile(r'(.)([A-Z][a-z]+)')
_p2 = _compile(r'([a-z0-9])([A-Z])')


def snake_case(name):
    """convert camel case to snake case"""
    return _p2.sub(r'\1_\2', _p1.sub(r'\1_\2', name)).lower()
