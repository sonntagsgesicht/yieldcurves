# -*- coding: utf-8 -*-

# yieldcurves
# -----------
# A Python library for financial yield curves.
#
# Author:   sonntagsgesicht
# Version:  0.1, copyright Thursday, 12 April 2023
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)

from .datetime import DAYS_IN_YEAR


from vectorizeit import vectorize

from ..tools.repr import repr_attr


def _day_count(start, end):
    r""" default day count function for rate period calculation

    :param start: period start date $t_s$
    :param end: period end date $t_e$
    :returns: year fraction $\tau(t_s, t_e)$
        from **start** to **end** as a float

    this default **day_count** function calculates the number of days
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


class Inv:

    def __init__(self, yf, domain=()):
        self._yf = yf
        self._inv = dict((yf(d), d) for d in domain)

    def __str__(self):
        return repr_attr(self, rstyle=False)

    def __repr__(self):
        return repr_attr(self, rstyle=True)

    @vectorize(keys=['x'])
    def __call__(self, x, y=None, *_, **__):
        # if not x:
        #     return self(y)
        if y is None:
            if x is None:
                return None
            if x in self._inv:
                return self._inv[x]
        raise NotImplementedError()


class YearFraction:

    def __init__(self, day_count=None, origin=None, domain=(),
                 date_type=float):
        # gather origin
        if origin is None:
            if domain:
                origin = domain[0]
            elif hasattr(date_type, 'today'):
                origin = date_type.today()
            else:
                origin = date_type()
        self.origin = origin

        # gather day_count
        if day_count is None:
            day_count = getattr(origin, 'day_count', None) or _day_count
        self.day_count = day_count

        self.inv = Inv(self, domain)

    def __str__(self):
        return repr_attr(self, rstyle=False)

    def __repr__(self):
        return repr_attr(self, rstyle=True)

    @vectorize(keys=['x'])
    def __call__(self, x, y=None, *_, **__):
        if y is None:
            if x is None:
                return None
            x, y = self.origin, x
        return self.day_count(x, y)
