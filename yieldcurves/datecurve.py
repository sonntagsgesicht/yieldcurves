from datetime import timedelta, date

from . import interpolation as _interpolation
from .tools.fit import simple_bracketing
from .tools.pp import prepr


DAYS_IN_YEAR = 365.25


def _yf(start, end):
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
    if hasattr(start, 'diff_in_days'):
        # duck typing businessdate.BusinessDate.diff_in_days
        return float(start.diff_in_days(end)) / DAYS_IN_YEAR
    diff = end - start
    if hasattr(diff, 'days'):
        # assume datetime.date or finance.BusinessDate (else days as float)
        return float(diff.days) / DAYS_IN_YEAR
    # use year fraction directly
    return float(diff)


class DateCurve:

    basedate = date(1900,1,1)
    cache = {}

    @property
    def domain(self):
        return tuple(self.__iter__())

    def __init__(self, curve, *, origin=None, yf=None):
        self.curve = curve
        self.origin = origin
        self.yf = yf

    def _yf(self, x):
        origin = self.origin or self.basedate
        yf = self.yf or _yf
        return yf(origin, x)

    def _inv(self, value, a=-1, b=300):
        if value not in self.cache:
            d = self.basedate
            for t in (100 * 365, 20 * 365, 365, 30, 1):
                while self._yf(d + timedelta(days=t)) < value:
                    d += timedelta(days=t)
            self.cache[value] = d
        return self.cache[value]

    def __str__(self):
        return prepr(self)

    def __repr__(self):
        return prepr(self)

    def __call__(self, *args, **kwargs):
        args = tuple(self._yf(x) for x in args)
        kwargs = {k: self._yf(y) for k, y in kwargs.items()}
        return self.curve(*args, **kwargs)

    def __getitem__(self, item):
        return self.curve[self._yf(item)]

    def __setitem__(self, key, value):
        self.curve[self._yf(key)] = value

    def __delitem__(self, key):
        del self.curve[self._yf(key)]

    def __iter__(self):
        return iter(self._inv(_) for _ in self.curve)


class DateCurveAdapter(DateCurve):

    class from_interpolation(DateCurve):
        def __init__(self, domain, curve, *, origin=None, yf=None,
                     interpolation=None, **kwargs):
            _yf = DateCurve(None, origin=origin, yf=yf)._yf
            xy_list = {_yf(x): y for x, y in zip(domain, curve)}
            interpolation = getattr(_interpolation, str(interpolation), interpolation)
            curve = type(curve)(xy_list.keys(), xy_list.values(), **kwargs)
            super().__init__(curve, origin=origin, yf=yf)
