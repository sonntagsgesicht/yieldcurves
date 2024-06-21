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
        m = f"\ndcf_curve.{a.__name__}({x}, {y})"
        m += f"\nyc_curve.{b.__name__}({x}, {y})"
        self.assertAlmostEqual(a(x, y), b(x, y), places=places, msg=m)

        x = y or x
        a = dcf_curve.get_cash_rate
        b = yc_curve.cash
        m = f"\ndcf_curve.{a.__name__}({x})"
        m += f"\nyc_curve.{b.__name__}({x})"
        self.assertAlmostEqual(a(x), b(x), places=places, msg=m)

    def all_rate_curve_test(self, dcf_curve, yc_curve, eps=1e-7, places=7):
        for d in self.domain:
            self.zero_rate_curve_test(dcf_curve, yc_curve, d or eps)
            self.zero_rate_curve_test(dcf_curve, yc_curve, 0, d or eps)
            for p in self.tenors:
                if d + p <= max(yc_curve.curve.x_list):
                    self.zero_rate_curve_test(dcf_curve, yc_curve, d, d + p)
            for p in self.periods:
                if d + p <= max(yc_curve.curve.x_list):
                    self.zero_rate_curve_test(dcf_curve, yc_curve, d, d + p)
            if d < max(yc_curve.curve):
                self.short_rate_curve_test(dcf_curve, yc_curve, d or eps)
            for p in self.tenors:
                if d + p <= max(yc_curve.curve.x_list):
                    self.cash_rate_curve_test(dcf_curve, yc_curve, d, d + p)

    def test_zero_rate_curve(self):

        yc_curve = yc.ZeroRate(self.curve, cash_frequency=None, frequency=None)
        dcf_curve = dcf.ZeroRateCurve(self.curve.x_list, self.curve.y_list,
                                      forward_tenor=.25, origin=0)
        dcf_curve._TIME_SHIFT = yc_curve.eps = eps = 1 /365

        f = stack()[0].function
        print(f"{f}.{yc_curve.curve=}")
        print(f"{f}.{dcf_curve=}")
        print(f"{f}.{yc_curve=}")

        self.all_rate_curve_test(dcf_curve, yc_curve, eps)


    def test_cash_rate_curve(self):
        yc_curve = yc.CashRate(self.curve, cash_frequency=None, frequency=None)
        dcf_curve = dcf.CashRateCurve(self.curve.x_list, self.curve.y_list,
                                     forward_tenor=.25, origin=0)
        dcf_curve._TIME_SHIFT = yc_curve.eps = eps = 1 /365

        f = stack()[0].function
        print(f"{f}.{yc_curve.curve=}")
        print(f"{f}.{dcf_curve=}")
        print(f"{f}.{yc_curve=}")

        self.cash_rate_curve_test(dcf_curve, yc_curve, eps)


    def test_short_rate_curve(self):
        curve = yc.interpolation.constant(self.curve.x_list, self.curve.y_list)
        yc_curve = yc.ShortRate(curve, cash_frequency=None, frequency=None)
        dcf_curve = dcf.ShortRateCurve(self.curve.x_list, self.curve.y_list,
                                     forward_tenor=.25, origin=0.)
        dcf_curve._TIME_SHIFT = yc_curve.eps = eps = 1 / 365

        f = stack()[0].function
        print(f"{f}.{yc_curve.curve=}")
        print(f"{f}.{dcf_curve=}")
        print(f"{f}.{yc_curve=}")

        self.short_rate_curve_test(dcf_curve, yc_curve, eps)
