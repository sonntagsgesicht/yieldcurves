from datetime import timedelta, date

from . import interpolation as _interpolation
from .yieldcurves import YieldCurve
from .tools.pp import pretty
from .tools import ITERABLE, inverse
from .tools.fit import simple_bracketing


@pretty
class DateCurveAdapter:

    BASEDATE = date.today()
    DAYS_IN_YEAR = 365.25
    INTERPOLATION = 'linear'
    _cache = {}

    def __init__(self, curve, *, origin=None, yf=None):
        self.curve = curve
        if not isinstance(origin, float) and isinstance(self.BASEDATE, date):
            origin = self._parse_date(origin)
        self.origin = origin
        self.yf = yf
        self._cache[self._cache_key] = self._cache.get(self._cache_key, {})

    def _parse_date(self, d):
        if d is None:
            return
        t = type(self.BASEDATE)
        if isinstance(d, t):
            return d
        if isinstance(d, date):
            d = d.isoformat()
        elif isinstance(d, int):
            d = str(d)
            d = f"{d[:4]}-{d[4:6]}-{d[6:8]}"
        if isinstance(d, str):
            return t.fromisoformat(d)
        if not isinstance(d, (list, tuple)):
            d = (d,)
        return t(*d)

    @property
    def _cache_key(self):
        return f"{self.origin} * {self.yf}"

    @staticmethod
    def dyf(start, end):
        r""" default year fraction function for rate period calculation

        :param start: period start date $t_s$
        :param end: period end date $t_e$
        :returns: year fraction $\tau(t_s, t_e)$
            from **start** to **end** as a float

        this default function calculates the number of days
        between $t_s$ and $t_e$ expressed as a fraction of a year, i.e.
        $$\tau(t_s, t_e) = \frac{t_e-t_s}{365.25}$$
        as an average year has nearly $365.25$ days.

        Since different date packages have different concepts to derive
        the number of days between two dates, **day_count** tries to adopt
        at least some of them. As there are:

        * dates given already as year fractions as a
          `float <https://docs.python.org/3/library/functions.html?#float>`_
          so $\tau(t_s, t_e) = t_e - t_s$.

        * `datetime <https://docs.python.org/3/library/datetime.html>`_
          the native Python package, so $\delta = t_e - t_s$ is a **timedelta**
          object with attribute **days** which is used.

        * `businessdate <https://pypi.org/project/businessdate/>`_
          a specialised package for banking business calendar
          and time period calculations,
          so the **BusinessDate** object **start** has a method
          **start.diff_in_days** which is used.

        """
        if isinstance(start, ITERABLE):
            return type(start)(DateCurve.dyf(s, end) for s in start)
        if isinstance(end, ITERABLE):
            return type(end)(DateCurve.dyf(start, e) for e in end)
        if hasattr(start, 'diff_in_days'):
            # duck typing businessdate.BusinessDate.diff_in_days
            return float(start.diff_in_days(end)) / DateCurve.DAYS_IN_YEAR
        diff = end - start
        if hasattr(diff, 'days'):
            # assume datetime.date or finance.BusinessDate (else days as float)
            return float(diff.days) / DateCurve.DAYS_IN_YEAR
        # use year fraction directly
        return float(diff)

    def year_fraction(self, x):
        if x is None:
            return None
        if isinstance(x, ITERABLE):
            return type(x)(self.year_fraction(_) for _ in x)
        origin = self.BASEDATE if self.origin is None else self.origin
        yf = self.yf or self.dyf
        y = yf(origin, x)
        self._cache[self._cache_key][y] = x
        return y

    def inverse(self, y):
        if isinstance(y, ITERABLE):
            return type(y)(self.year_fraction(_) for _ in y)
        if y not in self._cache[self._cache_key]:
            self._cache[self._cache_key][y] = self._inverse1(y)
        return self._cache[self._cache_key][y]

    def _inverse(self, value):
        raise NotImplementedError("this can fail with 'RecursionError'. "
                                  "please use _inverse2")
        # fails with RecursionError for
        # c = DateCurve(..., origin=date(2024, 6, 30), yf=get_30_360)
        # c._inverse(1.6694)
        d = self.BASEDATE if self.origin is None else self.origin
        if isinstance(d, (int, float)):
            def err(x):
                return self.year_fraction(d + x / self.DAYS_IN_YEAR) - value

            a = b = 0
            step = 365
            while 0 < err(a):
                a -= step
            while err(b) < 0:
                b += step
            m = simple_bracketing(err, a, b, 1 / 360)
            return d + m / self.DAYS_IN_YEAR
        else:
            def err(x):
                return self.year_fraction(d + timedelta(x)) - value

            a = b = 0
            step = 365
            while 0 <= err(a):
                a -= step
            while err(b) < 0:
                b += step
            try:
                m = simple_bracketing(err, a, b, 1 / 350)
            except RecursionError as e:
                print((value, self))
                raise e
            m = m if abs(err(m)) < abs(err(m + 1)) else m + 1
            return d + timedelta(m)

    def _inverse1(self, value, step=4096):
        d = self.BASEDATE if self.origin is None else self.origin
        if isinstance(d, (int, float)):
            def yf(x):
                return self.year_fraction(d + x / self.DAYS_IN_YEAR)

            return d + inverse(value, yf, step=step) / self.DAYS_IN_YEAR
        else:
            def yf(x):
                return self.year_fraction(d + timedelta(x))

            return d + timedelta(inverse(value, yf, step=step))

    def _inverse2(self, value):
        d = self.BASEDATE if self.origin is None else self.origin
        if isinstance(d, (int, float)):
            tdelta = (lambda t: float(max(1, int(t / 365))))
        else:
            tdelta = (lambda t: timedelta(days=t))

        delta = tdelta(3650)
        while value <= self.year_fraction(d):
            d -= delta

        times = 1461, 365, 90, 30, 7
        for t in times:
            delta = tdelta(t)
            while self.year_fraction(d + delta) < value:
                d += delta

        delta = tdelta(1)
        while self.year_fraction(d + delta) <= value:
            d += delta
        return d

    def __call__(self, *_, **__):
        _ = tuple(self.year_fraction(x) for x in _)
        __ = {k: self.year_fraction(y) for k, y in __.items()}
        return self.curve(*_, **__)

    def __getattr__(self, item):
        if hasattr(self.curve, item):
            def func(*args, **kwargs):
                args = tuple(self.year_fraction(x) for x in args)
                kwargs = {k: self.year_fraction(y) for k, y in kwargs.items()}
                return getattr(self.curve, item)(*args, **kwargs)
            func.__qualname__ = self.__class__.__qualname__ + '.' + item
            func.__name__ = item
            return func
        msg = f"{self.__class__.__name__!r} object has no attribute {item!r}"
        raise AttributeError(msg)

    @classmethod
    def from_interpolation(cls, domain, curve, *, origin=None, yf=None,
                           interpolation=None, curve_type=None, **kwargs):
        self = cls(None, origin=origin, yf=yf)

        curve_type = curve_type or YieldCurve
        curve_type = getattr(YieldCurve, str(curve_type), curve_type)

        interpolation = interpolation or cls.INTERPOLATION
        interpolation = \
            getattr(_interpolation, str(interpolation), interpolation)

        x_list = tuple(map(self.year_fraction, domain))
        y_list = tuple(map(curve, x_list)) if callable(curve) else curve
        self.curve = curve_type(interpolation(x_list, y_list), **kwargs)
        return self


class DateCurve(DateCurveAdapter):

    @property
    def _curve(self):
        curve = self.curve
        while hasattr(curve, 'curve'):
            curve = curve.curve
        return curve

    def __getitem__(self, item):
        return self._curve[self.year_fraction(item)]

    def __setitem__(self, key, value):
        self._curve[self.year_fraction(key)] = value

    def __delitem__(self, key):
        del self._curve[self.year_fraction(key)]

    def __iter__(self):
        return iter(map(self.inverse, self._curve))

    def __len__(self, item):
        return len(self._curve)

    def __contains__(self, item):
        return self.year_fraction(item) in self._curve
