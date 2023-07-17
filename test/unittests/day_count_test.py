from unittest import TestCase
from datetime import date

from businessdate import BusinessRange, BusinessDate

from yieldcurves.yieldcurves.daycount import DAYS_IN_YEAR, \
    YearFraction, _day_count as day_count
from .curve_tests import lin


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


class YearFractionUnitTests(TestCase):

    def test_float(self):
        self.assertEqual(YearFraction().origin, float())
        self.assertEqual(YearFraction(domain=[101.]).origin, 101.)
        t = -1
        d = lin(t, 10, 0.2)
        yf = YearFraction(origin=t)
        self.assertEqual(yf(None), None)
        self.assertEqual(yf.inv(None), None)
        self.assertRaises(NotImplementedError, yf.inv, 3.33)
        for s, e in zip(d[:-1], d[1:]):
            a = yf(s, e)
            b = day_count(s, e)
            self.assertEqual(a, b)
        s = t + 3.3
        yf = YearFraction(origin=s, domain=d)
        for e in d:
            a = yf(e)
            b = day_count(s, e)
            self.assertEqual(a, b)
            self.assertAlmostEqual(yf.inv(a), e)
        dc = (lambda s, e: s + e)
        yf = YearFraction(origin=101, day_count=dc, domain=d)

        for s, e in zip(d[:-1], d[1:]):
            a = yf(s, e)
            b = dc(s, e)
            self.assertEqual(a, b)

        s = yf.origin
        for e in d:
            a = yf(e)
            b = dc(s, e)
            self.assertEqual(a, b)
            self.assertAlmostEqual(yf.inv(a), e)

    def test_date(self):
        self.assertEqual(
            YearFraction(date_type=date).origin, date.today())

    def test_businessdate(self):
        self.assertEqual(
            YearFraction(date_type=BusinessDate).origin, BusinessDate())
        t = BusinessDate(20231101)
        d = BusinessRange(t, t + '5y', '4m')
        yf = YearFraction(origin=t)
        for s, e in zip(d[:-1], d[1:]):
            a = yf(s, e)
            b = day_count(s, e)
            self.assertEqual(a, b)
        yf = YearFraction(origin=s, domain=d)
        for e in d:
            a = yf(e)
            b = day_count(s, e)
            self.assertEqual(a, b)
            self.assertAlmostEqual(yf.inv(a), e)
