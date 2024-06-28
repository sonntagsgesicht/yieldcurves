from unittest import TestCase
from datetime import date

from businessdate import BusinessRange, BusinessDate
from businessdate import daycount as dcc

from yieldcurves.datecurve import DateCurve
from yieldcurves.tools import lin, AlgebraCurve


day_count = DateCurve.dyf
DAYS_IN_YEAR = DateCurve.DAYS_IN_YEAR


class DefaultYearFrachtionUnitTests(TestCase):

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


class YearFrachtionInverseUnitTests(TestCase):

    def test_inverse(self):
        for day_count in dir(dcc):
            if not day_count.startswith('get'):
                continue
            if day_count.startswith('get_act_act_icma'):
                continue
            if day_count.startswith('get_rational_period'):
                continue
            day_count = getattr(dcc, day_count)
            today = BusinessDate(20240630)
            curve = AlgebraCurve()
            a = DateCurve(curve, origin=today, yf=day_count)
            for d in BusinessRange(today, '2y', '3d'):
                if '360' in str(a.year_fraction):
                    if d.day in (30, 31):
                        continue
                    if d.month == 2 and d.day in (28, 29, 30, 31):
                        continue

                f = a.year_fraction(d)
                p = a.inverse(f)
                q = a.inverse(f)
                g = a.year_fraction(p)

                self.assertEqual(p, q, msg=(d, a))
                self.assertEqual(d, p, msg=(d, a))
                self.assertEqual(f, g, msg=(d, a))




class DateCurveUnitTests(TestCase):

    def test_float(self):
        ...

    def test_date(self):
        ...

    def test_businessdate(self):
        ...
