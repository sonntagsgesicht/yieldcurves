
from .. import interpolation as _interpolation
from ..interpolation import linear, base_interpolation


def simple_bracketing(func, a, b, precision=1e-13):
    """ find root by _simple_bracketing an interval

    :param callable func: function to find root
    :param float a: lower interval boundary
    :param float b: upper interval boundary
    :param float precision: max accepted error
    :rtype: tuple
    :return: :code:`(a, m, b)` of last recursion step
        with :code:`m = a + (b-a) *.5`

    """
    fa, fb = func(a), func(b)
    if fb < fa:
        f = (lambda x: -func(x))
        fa, fb = fb, fa
    else:
        f = func

    if not fa <= 0. <= fb:
        msg = "simple_bracketing function must be loc monotone " \
              "between %0.4f and %0.4f \n" % (a, b)
        msg += "and simple_bracketing 0. between  %0.4f and %0.4f." % (fa, fb)
        raise AssertionError(msg)

    m = a + (b - a) * 0.5
    if abs(b - a) < precision and abs(fb - fa) < precision:
        return a, m, b

    a, b = (m, b) if f(m) < 0 else (a, m)
    return simple_bracketing(f, a, b, precision)




def fit(cls, x_list, y_list=None, *, interpolation=linear,
        method='__call__', a=None, b=None, precision=None, **kwargs):
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

        >>> from yieldcurves.tools.stripping import fit
        >>> from yieldcurves import ZeroRate
        >>> domain = 1, 2, 3, 5, 10, 15, 20, 30
        >>> rates =  .01, .013, .017, .015, .014, .012, .015, .015

        >>> fit(ZeroRate, domain, rates)
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

    self = cls(curve)
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
