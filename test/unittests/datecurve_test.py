from unittest import TestCase
from datetime import date

from businessdate import BusinessRange, BusinessDate

from yieldcurves.datecurve import DateCurve
from yieldcurves.tools import lin


day_count = DateCurve.dyf
DAYS_IN_YEAR = DateCurve.DAYS_IN_YEAR


class DayCountUnitTests(TestCase):

    def test_float(self):
        t = -1
        d = lin(t, 10, 0.2)
        for s, e in zip(d[:-1], d[1:]):
            self.assertEqual(e - s, day_count(s, e))
        s = t
        for e in d:
            a = e - s
            b = day_count(s, e)
            self.assertEqual(a, b)

    def test_date(self):
        t = BusinessDate(20220101)
        d = BusinessRange(t, '5y', '9w')
        d = [dd.to_date() for dd in d]
        for s, e in zip(d[:-1], d[1:]):
            a = (e - s).days / DAYS_IN_YEAR
            b = day_count(s, e)
            self.assertEqual(a, b)
        s = t.to_date()
        for e in d:
            a = (e - s).days / DAYS_IN_YEAR
            b = day_count(s, e)
            self.assertEqual(a, b)

    def test_businessdate(self):
        t = BusinessDate(20220101)
        d = BusinessRange(t, t + '5y', step='9w')
        for s, e in zip(d[:-1], d[1:]):
            a = s.diff_in_days(e) / DAYS_IN_YEAR
            b = day_count(s, e)
            self.assertEqual(a, b)
        s = t
        for e in d:
            a = s.diff_in_days(e) / DAYS_IN_YEAR
            b = day_count(s, e)
            self.assertEqual(a, b)
