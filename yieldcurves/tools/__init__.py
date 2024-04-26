from scipy.integrate import quad as _integrate  # noqa F401
from .ap3 import plot as ascii_plot  # noqa F401

EPS = 1 / 250
ITERABLE = list, tuple


# integrate = (lambda c, x, y: _integrate(c, float(x), float(y)))
integrate = _integrate


def lin(start, stop, step):
    if start + step < start < stop or stop < start < start + step:
        raise ValueError()
    r = [start]
    while r[-1] + step < stop:
        r.append(r[-1] + step)
    return r
