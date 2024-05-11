# -*- coding: utf-8 -*-

# yieldcurves
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.4, copyright Saturday, 10 October 2020
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)

from inspect import stack
from unittest import TestCase

from businessdate import BusinessDate, BusinessRange
import dcf
import yieldcurves as yc


class RateCurveUnitTests(TestCase):
    def setUp(self):
        today = BusinessDate()
        domain = list(BusinessRange(today, today + '10Y', '3M'))
        domain[-1] = today + '99y'

        periods = '1D', '2B', '8D', '2W', '14B', '1M', '1M1D', '3M', '6M', \
            '6M2W1D', '9M', '12M', '1Y', '2Y', '5Y', '5Y3M', '10Y', '11Y3M', \
            '15Y', '17Y1W', '20Y', '20Y1D', '25Y', '30Y', '33Y1M1W1D', '70Y'
        rates = [0.02, 0.018, 0.016, 0.015, 0.017, 0.019]

        #periods = '1D', '2B', '8D', '2W', '14B', '1M', '1M1D',
        #rates = [0.02]
        points = (rates * len(domain))[:len(domain)]

        self.domain = [today.get_day_count(d) for d in domain]
        self.periods = [today.get_day_count(d) for d in periods]
        self.tenors = [1/12, 1/4, 1/2, 1.]
        self.curve = yc.interpolation.linear(self.domain, points)

    def zero_rate_curve_test(self, dcf_curve, yc_curve, x, y=None, places=7):

        a = dcf_curve.get_discount_factor
        b = yc_curve.df
        m = f"\ndcf_curve.{a.__name__}({x}, {y})"
        m += f"\nyc_curve.{b.__name__}({x}, {y})"
        self.assertAlmostEqual(a(x, y), b(x, y), places=places, msg=m)

        a = dcf_curve.get_zero_rate
        b = yc_curve.zero
        m = f"\ndcf_curve.{a.__name__}({x}, {y})"
        m += f"\nyc_curve.{b.__name__}({x}, {y})"
        self.assertAlmostEqual(a(x, y), b(x, y), places=places, msg=m)

    def short_rate_curve_test(self, dcf_curve, yc_curve, x, y=None, places=7):

        x = y or x
        a = dcf_curve.get_short_rate
        b = yc_curve.short
        m = f"\ndcf_curve.{a.__name__}({x})"
        m += f"\nyc_curve.{b.__name__}({x})"
        self.assertAlmostEqual(a(x), b(x), places=places, msg=m)

    def cash_rate_curve_test(self, dcf_curve, yc_curve, x, y=None, places=7):

        a = dcf_curve.get_cash_rate
        b = yc_curve.cash
        m = f"\nyc_curve.{b.__name__}({x}, {y})"
        self.assertAlmostEqual(a(x, y), b(x, y), places=places, msg=m)

        x = y or x
        a = dcf_curve.get_cash_rate
        b = yc_curve.cash
        m = f"\nyc_curve.{b.__name__}({x})"
        self.assertAlmostEqual(a(x), b(x), places=places, msg=m)

    def test_zero_rate_curve(self):

        yc_curve = yc.ZeroRate(self.curve, cash_frequency=None)
        dcf_curve = dcf.ZeroRateCurve(self.curve.x_list, self.curve.y_list,
                                      forward_tenor=.25)
        dcf_curve._TIME_SHIFT = yc_curve.eps = eps = 1 /365

        print(f"{yc_curve.curve=}")
        print(f"{dcf_curve=}")
        print(f"{yc_curve=}")

        for d in self.domain:
            self.zero_rate_curve_test(dcf_curve, yc_curve, d or eps)
            self.zero_rate_curve_test(dcf_curve, yc_curve, 0, d or eps)
            for p in self.tenors:
                if max(yc_curve.curve.x_list) < d + p:
                    continue
                self.zero_rate_curve_test(dcf_curve, yc_curve, d, d + p)
            for p in self.periods:
                if max(yc_curve.curve.x_list) < d + p:
                    continue
                self.zero_rate_curve_test(dcf_curve, yc_curve, d, d + p)

    def test_cash_rate_curve(self):
        dcf_curve = dcf.CashRateCurve(
            self.domain, self.points, origin=self.today, forward_tenor='3M')
        yc_curve = yc.CashRateCurve(
            self.domain, self.points, origin=self.today, forward_tenor='3M')

        curve_a = dcf_curve
        curve_b = yc_curve
        curve_b.curve.frequency = None
        for d in self.domain:
            for p in self.periods:
                x = d + p
                a = curve_a.get_cash_rate(x)
                b = curve_b.get_cash_rate(x)
                self.assertAlmostEqual(a, b, msg=str(x))

    def test_short_rate_curve(self):
        dcf_curve = dcf.ShortRateCurve(
            self.domain, self.points, origin=self.today, forward_tenor='3M')
        dcf_curve._TIME_SHIFT = '6m'
        yc_curve = yc.ShortRateCurve(
            self.domain, self.points, origin=self.today, forward_tenor='3M')
        self._rate_curve_test(dcf_curve, yc_curve)
