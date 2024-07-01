# -*- coding: utf-8 -*-

# yieldcurves
# -----------
# A Python library for financial yield curves.
#
# Author:   sonntagsgesicht
# Version:  0.1, copyright Saturday, 22 April 2023
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


from datetime import timedelta, date

from . import interpolation as _interpolation
from .yieldcurves import YieldCurve
from .tools.pp import pretty
from .tools import ITERABLE
from .tools.fit import simple_bracketing, inverse


@pretty
class DateCurve:
    BASEDATE = date.today()
    DAYS_IN_YEAR = 365.25
    INTERPOLATION = 'linear'
    _cache = {}

    def __init__(self, curve, *, origin=None, yf=None):
        """Curve class with date type arguments

        :param curve: inner curve with float arguments
        :param origin: curve start date
            (optional, default is |DateCurve.BASEDATE|)
        :param yf: year fraction callable `yf(start: date, end: date) -> float`
            to derive float argument **y** from a date **x** via
            `y = yf(origin, x)`.
            (optional, default is *actual/365.25*)

        >>> from datetime import date
        >>> from yieldcurves import DateCurve, eye

        >>> yc = DateCurve(eye(), origin=date(2024,1,1))
        >>> yc(date(2025,1,1))
        1.002053388090349

        >>> from businessdate import BusinessDate  # date extension for finance
        >>> from businessdate.daycount import get_30_360  # handles date

        >>> yc = DateCurve(eye(), origin=date(2024,1,1), yf=get_30_360)
        >>> yc(date(2025,1,1))
        1.0
        >>> yc(BusinessDate(20250101))  # BusinessDate behaves like date
        1.0

        >>> byc = DateCurve(eye(), origin=BusinessDate(20240101), yf=get_30_360)
        >>> byc(BusinessDate(20250101))
        1.0

        """

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
            # diff_years = date(end.year, 12, 31) - date(start.year, 1, 1)
            # return float(start.diff_in_days(end)) / diff_years.days
        diff = end - start
        if hasattr(diff, 'days'):
            # assume datetime.date or finance.BusinessDate (else days as float)
            return float(diff.days) / DateCurve.DAYS_IN_YEAR
            # diff_years = date(end.year, 12, 31) - date(start.year, 1, 1)
            # return float(diff.days / diff_years.days)
        # use year fraction directly
        return float(diff)

    def year_fraction(self, x):
        """year fraction function

        :param x: date argument
        :return: float result

        calculates year fraction **y** of period from **origin** and **x** as
        `y = yf(origin, x)` with **yf** as given.

        **yf** defaults to |DateCurve().dyf()| and
        **origin** defaults to |DateCurve.BASEDATE|

        >>> from businessdate import BusinessRange, BusinessDate
        >>> from businessdate.daycount import get_act_act
        >>> from yieldcurves import DateCurve, eye

        >>> today = BusinessDate(20240101)
        >>> yc = DateCurve(eye(), origin=today, yf=get_act_act)

        >>> yc.year_fraction(today)
        0.0

        >>> yc.year_fraction(today + '1w')
        0.01912568306010929

        >>> yc.year_fraction(today + '1m')
        0.08469945355191257

        >>> yc.year_fraction(today + '3m')
        0.24863387978142076

        >>> yc.year_fraction(today + '1y')
        1.0

        """
        if x is None:
            return None
        if isinstance(x, ITERABLE):
            return type(x)(self.year_fraction(_) for _ in x)
        origin = self.BASEDATE if self.origin is None else self.origin
        yf = self.yf or self.dyf
        date_type = type(origin)
        if not isinstance(x, date_type):
            x = date_type(x)
        y = yf(origin, x)
        self._cache[self._cache_key][y] = x
        return y

    def inverse(self, y):
        """inverse function of year fraction function

        :param y: float argument
        :return: date result with `y = yf(origin, x)`

        as year fraction functions are in general not injektiv,
        i.e. have unique relation between input and output
        s.th. there are dates **a** and **b** with

            `yf(origin, a) = yf(origin, b)`

        Hence, this method provides the smallest date **x**
        s.th. `y = yf(origin, x)`.

        Note, this method relies heavily on caching and caches also results of
        |DateCurve().year_fraction()| which might result in conflicts to
        the late minimal condition.

        >>> from businessdate import BusinessDate
        >>> from businessdate.daycount import get_30_360
        >>> from yieldcurves import DateCurve, eye

        >>> today = BusinessDate(20241231)
        >>> yc = DateCurve(eye(), origin=today, yf=get_30_360)
        >>> yc.inverse(1.7)
        BusinessDate(20260912)

        >>> yc.inverse(0.25)
        BusinessDate(20250331)

        >>> yc.inverse(1.7)
        BusinessDate(20260912)

        >>> y = yc.year_fraction(BusinessDate(20250331))
        >>> y
        0.25

        >>> yc.inverse(y)
        BusinessDate(20250331)

        >>> yc._cache[yc._cache_key] = {}  # this clears the cache
        >>> y = yc.year_fraction(BusinessDate(20250101))
        >>> y
        0.002777777777777778

        >>> yc.inverse(y)
        BusinessDate(20250101)

        """
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
        """

        :param list[date] domain: curve date list
        :param list[float] curve: curve values or callable
            if callable then values of curve at points of domain are used
        :param date origin: curve start date
            (optional, default is |DateCurve.BASEDATE|)
        :param Callable yf:
            year fraction callable `yf(start: date, end: date) -> float`
            to derive float argument **y** from a date **x** via
            `y = yf(origin, x)`.
            (optional, default is *actual/365.25*)
        :param interpolation: interpolation class to build
            `interpolation(domain, curve)`
            to give inner curve, i.e. turning **domain** and **curve**
            into a callable turning **float** into **float**.
            (optional, default is |linear|)
        :param [str, type] curve_type: type of curve
            (optional, default is |YieldCurve|)
        :param dict kwargs: additional arguments for curve type creation
        :return: DateCurve with inner curve of **curve_type**

        builds |DateCurve| with interpolated inner curve.

        >>> from businessdate import BusinessDate, BusinessRange
        >>> from yieldcurves import DateCurve, YieldCurve
        >>> from yieldcurves.interpolation import linear

        >>> today = BusinessDate(20240101)
        >>> domain = BusinessRange(today, today + '6y', '1y')
        >>> values = 0.02, 0.022, 0.021, 0.019, 0.02
        >>> curve_type = YieldCurve.from_short_rates
        >>> yc = DateCurve.from_interpolation(domain, values, origin=today, curve_type=curve_type)
        >>> yc
        DateCurve(YieldCurve.from_short_rates(linear([0.0, 1.002053388090349, 2.001368925393566, 3.0006844626967832, 4.0], [0.02, 0.022, 0.021, 0.019, 0.02])), origin=BusinessDate(20240101))

        >>> yc(today + '6m')
        0.020497267759562843

        >>> yc.spot(today + '6m')
        0.020497267759562673

        """  # noqa 501
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

    # --- dict like properties ---

    @property
    def _curve(self):
        """get innermost curve

        :return: innermost curve
        """
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

    def update(self, other):
        """updates innermost curve

        :param other: dict
        :return: DateCurve
        """
        other = {self.year_fraction(x): y for x, y in other.items()}
        self._curve.update(other)
