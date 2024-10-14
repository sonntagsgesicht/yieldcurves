# -*- coding: utf-8 -*-

# yieldcurves
# -----------
# A Python library for financial yield curves.
#
# Author:   sonntagsgesicht
# Version:  0.2.6.1, copyright Monday, 14 October 2024
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


from re import compile as _compile
from warnings import warn

try:
    from curves import init, Curve  # noqa E401 E402
    from curves.numerics import (integrate,  # noqa E401 E402
                                 bisection_method,  # noqa E401 E402
                                 newton_raphson,  # noqa E401 E402
                                 secant_method)  # noqa E401 E402
except ImportError as e:
    warn(str(e))
    init = bisection_method = newton_raphson = secant_method = \
        integrate = lambda *_, **__: None
    Curve = object


try:
    from prettyclass import prettyclass
except ImportError as e:
    warn(str(e))
    prettyclass = (lambda cls=None, *_, **__:
                   cls if cls else (lambda cls: cls))


try:
    from vectorizeit import vectorize
except ImportError as e:
    warn(str(e))
    vectorize = (lambda cls=None, *_, **__:
                 print if cls else (lambda cls: print))


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
