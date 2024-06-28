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
    return _p2.sub(r'\1_\2', _p1.sub(r'\1_\2', name)).lower()


def inverse(y, func, step=1):
    """inverse of `y` under a strict monotone `func(x: int) -> float`"""
    x = 0
    step = int(step) or 1
    if func(x + step) < func(x):
        return inverse(y, lambda x: -1 * func(x), step=step)
    while y < func(x - step):
        step *= 2
    x -= step
    if y == func(x):
        return x
    while 0 < step:
        while func(x + step) < y:
            x += step
        step //= 2
    if y == func(x):
        return x
    while func(x + 1) <= y:
        x += 1
    return x if y - func(x) < func(x + 1) - y else x + 1
