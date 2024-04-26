

from . import interpolation as _interpolation
from .tools.adapter import CurveAdapter
# from .adapter import ZeroRate as CompoundingRate, SwapParRate


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


fit = simple_bracketing


class StrippedSwapCurve:

    def __init__(self, curve, frequency=None, interpolation='linear',
                 domain=(), precision=None, **__):
        # todo: better use _inner for curve and let swap par rates tobe
        self.curve = curve
        i_type = getattr(_interpolation, str(interpolation), interpolation)
        domain = tuple(domain or self)
        data = tuple(self.curve(d) for d in domain)
        r = i_type(domain, data, **__)
        # self._inner = CompoundingRate(r, frequency=frequency)
        self._inner = CurveAdapter(r)
        # self._stripped = SwapParRate(self._inner, frequency=frequency)
        self._stripped = CurveAdapter(self._inner)

        self.frequency = frequency
        self.interpolation = getattr(i_type, '__name__', str(interpolation))
        self.precision = precision

        self._fit(precision or 1e-13)

    def _fit(self, precision=None):
        for p in self._inner:
            e = self._stripped(p) - self.curve(p)
            if precision < abs(e):
                def err(_):
                    self._inner[p] = _
                    return self._stripped(p) - self.curve(p)
                fit(err, -2 * self.curve(p), 2 * self.curve(p), precision)

    def __call__(self, x, y=None):
        return self._inner(x, y)


class StrippedRateCurve:

    def __init__(self, curve, frequency=None, interpolation='linear',
                 domain=(), precision=None,
                 yield_curve=None, **__):
        yield_curve = yield_curve or curve
        curve = curve or yield_curve

        domain = tuple(domain or self)
        i_type = getattr(_interpolation, str(interpolation), interpolation)
        data = tuple(curve(d) for d in domain)
        rate_curve = i_type(domain, data, **__)
        #rate_curve = CompoundingRate(rate_curve, frequency=frequency)
        rate_curve = CurveAdapter(rate_curve)
        #stripped_curve = SwapParRate(rate_curve, frequency=frequency)
        stripped_curve = CurveAdapter(rate_curve)

        self.curve = rate_curve

        self._source = yield_curve
        self._target = stripped_curve

        self.frequency = frequency
        self.interpolation = getattr(i_type, '__name__', str(interpolation))
        self.precision = precision

        self._fit(precision or 1e-13)

    def _fit(self, precision=None):
        for p in self:
            e = self._target(p) - self._source(p)
            if precision < abs(e):
                def err(_):
                    self[p] = _
                    return self._target(p) - self._source(p)
                fit(err, -2 * self.curve(p), 2 * self(p), precision)
