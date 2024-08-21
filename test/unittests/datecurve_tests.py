from unittest import TestCase

from businessdate import BusinessRange, BusinessDate
from businessdate import daycount as dcc

from yieldcurves.datecurves import DateCurve
from yieldcurves.interpolation import linear
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

                x = a.inverse(f)
                # self.assertEqual(x, a._inverse(f), msg=(d, a))
                self.assertEqual(x, a._inverse1(f), msg=(d, a))
                self.assertEqual(x, a._inverse2(f), msg=(d, a))


class DateCurveUnitTests(TestCase):

    def test_float(self):
        c = linear([0, 1, 10, 100], [10, 0, 0, 0])
        d = DateCurve(c, origin=0.)
        d.year_fraction(c.x_list)
        d[0.5] = 2
        self.assertEqual(c[0.5], 2)
        self.assertEqual(c[0.5], d[0.5])
        self.assertEqual(c.x_list, list(d))
        self.assertEqual(d(2), 0)
        del d[0.5]
        d[0.15] = 0
        self.assertEqual(d(2), 0)

    def test_date(self):
        c = linear([0, 1], [10, 0])
        origin = BusinessDate()
        d = DateCurve(
            c, origin=origin.to_date(), yf=getattr(dcc, 'get_30_360'))
        d[origin + '3m'] = 7
        d[origin + '9m'] = 3
        self.assertEqual(d(origin + '3m'), 7)
        self.assertEqual(d(origin + '6m'), 5)
        self.assertEqual(d(origin + '9m'), 3)
        self.assertEqual(c[0.25], d[origin + '3m'])

    def test_businessdate(self):
        c = linear([0, 1], [10, 0])
        origin = BusinessDate(20240630)
        DateCurve.BASEDATE = BusinessDate()
        d = DateCurve(c, origin=origin, yf=getattr(dcc, 'get_30_360'))
        d[d.origin + '3m'] = 7
        d[d.origin + '9m'] = 3
        self.assertEqual(d(d.origin + '3m'), 7)
        self.assertEqual(d(d.origin + '6m'), 5)
        self.assertEqual(d(d.origin + '9m'), 3)
        self.assertEqual(c[0.25], d[origin + '3m'])

    def test_interpolation(self):
        origin = BusinessDate(20240630)
        DateCurve.BASEDATE = BusinessDate()
        dates = origin + ['0d', '12m']
        d = DateCurve.from_interpolation(
            dates, [10, 0], origin=origin, yf=getattr(dcc, 'get_30_360'))
        d[d.origin + '3m'] = 7
        d[d.origin + '9m'] = 3
        self.assertEqual(d(d.origin + '3m'), 7)
        self.assertEqual(d(d.origin + '6m'), 5)
        self.assertEqual(d(d.origin + '9m'), 3)
        for x in BusinessRange(origin, '2y', '1m1d'):
            y = d.year_fraction(x)
            self.assertAlmostEqual(d._curve(y), d(x))
        c = linear([0.0, 0.25, 0.75, 1.0], [10.0, 7.0, 3.0, 0.0])
        self.assertAlmostEqual(d._curve.x_list, c.x_list)
        self.assertAlmostEqual(d._curve.y_list, c.y_list)
