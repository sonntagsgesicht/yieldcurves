# -*- coding: utf-8 -*-

# yieldcurves
# -----------
# A Python library for financial yield curves.
#
# Author:   sonntagsgesicht
# Version:  0.2.2, copyright Thursday, 22 August 2024
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


from re import compile as _compile
from .mpl import plot, lin  # noqa F401
from .algebra import AlgebraCurve  # noqa F401
from .numerics import integrate  # noqa F401


EPS = 1 / 365.25
ITERABLE = list, tuple


_p1 = _compile(r'(.)([A-Z][a-z]+)')
_p2 = _compile(r'([a-z0-9])([A-Z])')


def snake_case(item, sep='_'):
    """convert camel case to snake case"""
    item = _p2.sub(r'\1_\2', _p1.sub(r'\1_\2', item))
    return item.lower().replace('_', sep)


def camel_case(item: str, first_lower=False):
    item = "".join(x.capitalize() for x in item.lower().split("_"))
    return item[0].lower() + item[1:] if first_lower else item
