from datetime import timedelta, date

from . import interpolation as _interpolation
from .yieldcurves import YieldCurve
from .tools.pp import pretty
from .tools import ITERABLE, inverse
from .tools.fit import simple_bracketing


@pretty
class DateCurve:

    BASEDATE = date.today()
    DAYS_IN_YEAR = 365.25
    INTERPOLATION = 'linear'

    def __init__(self, curve, *, origin=None, yf=None):
        self.curve = curve
        self.origin = origin
        self.yf = yf
        self._cache = {'__hash__': f"{self.origin} * {self.yf}"}

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
        return yf(origin, x)

    def inverse(self, value):
        if isinstance(value, ITERABLE):
            return type(value)(self.year_fraction(_) for _ in value)

        if not f"{self.origin} * {self.yf}" == self._cache.get('__hash__', ''):
            self._cache = {'__hash__': f"{self.origin} * {self.yf}"}

        if value not in self._cache:
            self._cache[value] = self._inverse2(value)
        return self._cache[value]

    def _inverse(self, value):
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
            return d + \
                simple_bracketing(err, a, b, 1 / 360) / self.DAYS_IN_YEAR
        else:
            def err(x):
                return self.year_fraction(d + timedelta(x)) - value
            a = b = 0
            step = 365
            while 0 < err(a):
                a -= step
            while err(b) < 0:
                b += step
            return d + timedelta(simple_bracketing(err, a, b, 1 / 350))

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
            tdelta = (lambda t: float(max(1, int(t/365))))
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

    def __call__(self, *args, **kwargs):
        # args = tuple(map(self._yf, args))
        # dict(map(lambda x, y: (x, self._yf(y), kwargs.items())))
        args = tuple(self.year_fraction(x) for x in args)
        kwargs = {k: self.year_fraction(y) for k, y in kwargs.items()}
        return self.curve(*args, **kwargs)

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

    def __getitem__(self, item):
        return self.curve[self.year_fraction(item)]

    def __setitem__(self, key, value):
        self.curve[self.year_fraction(key)] = value

    def __delitem__(self, key):
        del self.curve[self.year_fraction(key)]

    def __iter__(self):
        return iter(map(self.inverse, self.curve))

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
