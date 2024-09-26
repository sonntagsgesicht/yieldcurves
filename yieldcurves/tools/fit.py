# -*- coding: utf-8 -*-

# yieldcurves
# -----------
# A Python library for financial yield curves.
#
# Author:   sonntagsgesicht
# Version:  0.2.2, copyright Thursday, 22 August 2024
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


from ..interpolation import linear, base_interpolation


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


def simple_bracketing(func, a, b, precision=1e-13, mid=None, vprecision=None):
    """ find root by _simple_bracketing an interval

    :param callable func: function to find root
    :param float a: lower interval boundary
    :param float b: upper interval boundary
    :param float precision: max accepted error
    :rtype: float
    :return: :code:`a + (b-a) *.5` of last recursion step

    """

    fa, fb = func(a), func(b)
    if fb < fa:
        f = (lambda x: -func(x))
        fa, fb = fb, fa
    else:
        f = func

    if not fa <= 0. <= fb:
        msg = "simple_bracketing function must be loc monotone " \
              f"between {a} and {b} " \
              f"and simple_bracketing 0. between {fa} and {fb}."
        raise AssertionError(msg)

    m = a + (b - a) * 0.5 if mid is None else mid(a, b)

    if abs(b - a) < (vprecision or 1e-14):
        msg = "no solution found."\
              "simple_bracketing function must be loc monotone " \
              f"between {a} and {b} " \
              f"and simple_bracketing 0. between {fa} and {fb}."
        raise AssertionError(msg)

    if abs(fb - fa) < precision:
        return m

    a, b = (m, b) if f(m) < 0 else (a, m)
    return simple_bracketing(f, a, b, precision, vprecision=vprecision)


def fit(self, x_list, y_list=None, *, interpolation=linear,
        method='__call__', a=None, b=None, precision=1e-13, **kwargs):
    """fit curve to meet given values at points in domain

    :param cls curve class
    :param x_list: points to meet values at
        (or inner curve of type `base_interpolation`)
    :param y_list: values to meet
        (optional; default `__call__`)
    :param interpolation: interpolation method
        with signature `interpolation(x_list, y_list, **kwargs)
        (optional; default `linear`)
    :param method: method to calculate values at `x_list`
        (optional; default `__call__`)
    :param float a: lower interval boundary (see `simple_bracketing`)
    :param float b: upper interval boundary (see `simple_bracketing`)
    :param float precision: max accepted error (see `simple_bracketing`)
    :return: fitted curve object of type `cls`

        >>> from yieldcurves.tools.fit import fit
        >>> from yieldcurves import YieldCurve
        >>> domain = 1, 2, 3, 5, 10, 15, 20, 30
        >>> rates =  .01, .013, .017, .015, .014, .012, .015, .015

        >>> fit(YieldCurve(), domain, rates)
        ZeroRate(linear([1, ..., 30], [0.01, ..., 0.015]))

    """
    if isinstance(x_list, base_interpolation):
        curve = x_list
        x_list = curve.x_list
        y_list = curve.y_list
    else:
        if isinstance(interpolation, str):
            interpolation = getattr(locals(), interpolation)
        curve = interpolation(x_list, y_list, **kwargs)

    setattr(self, 'curve', curve)
    func = getattr(self, str(method), method)
    for p, v in zip(x_list, y_list):
        def err(_):
            curve[p] = _
            return v - func(p)
        if a is None:
            a = -2 * v
        if b is None:
            b = 2 * v
        simple_bracketing(err, a, b, precision)
    return self


def _fit(dct, source, target, a=None, b=None, precision=None):
    # dct.keys = ZeroRate.curve.domain
    # dct.values = ZeroRate.curve
    # source = ZeroRate.par
    # target = InterestRateAdapter.par
    for p in dct:
        if abs(target(p) - source(p)) < precision:
            continue

        def err(_):
            dct[p] = _
            return target(p) - source(p)
        if a is None:
            a = -2 * source(p)
        if b is None:
            b = 2 * source(p)

        simple_bracketing(err, a, b, precision)
