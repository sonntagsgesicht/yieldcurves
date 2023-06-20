# -*- coding: utf-8 -*-

# yieldcurves
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.4, copyright Saturday, 10 October 2020
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


from unittest import TestCase

from businessdate import BusinessDate, BusinessRange
import dcf
import yieldcurves as yc


class RateCurveUnitTests(TestCase):
    def setUp(self):
        self.today = BusinessDate()
        self.domain = tuple(BusinessRange(self.today, self.today + '1Y', '3M'))
        self.len = len(self.domain)
        self.periods = '1D', '2B', '8D', '2W', '14B', '1M', '1M1D', \
                       '3M', '6M', '6M2W1D', '9M', '12M', '1Y', '2Y', '5Y', \
                       '5Y3M', '10Y', '30Y', '70Y'
        # self.periods = '1D', '2B', '8D', '2W', '14B', '1M', '1M1D',
        rates = [0.02, 0.018, 0.015, 0.017]
        rates = [0.02]
        points = rates * len(self.domain)
        self.points = points[:len(self.domain)]

    def _rate_curve_test(self, curve_a, curve_b, places=7):

        for d in self.domain:
            for p in self.periods:
                x = d + p
                a = curve_a.get_discount_factor(x, x)
                b = curve_b.get_discount_factor(x, x)
                self.assertAlmostEqual(a, b, places=places, msg=str(x))

                a = curve_a.get_discount_factor(x)
                b = curve_b.get_discount_factor(x)
                self.assertAlmostEqual(a, b, places=places, msg=str(x))

                a = curve_a.get_zero_rate(x)
                b = curve_b.get_zero_rate(x)
                self.assertAlmostEqual(a, b, places=places, msg=str(x))

                a = curve_a.get_short_rate(x)
                b = curve_b.get_short_rate(x)
                self.assertAlmostEqual(a, b, places=places, msg=str(x))

                a = curve_a.get_cash_rate(x)
                b = curve_b.get_cash_rate(x)
                self.assertAlmostEqual(a, b, places=places, msg=str(x))

    def test_zero_rate_curve(self):
        dcf_curve = dcf.ZeroRateCurve(
            self.domain, self.points, origin=self.today, forward_tenor='3M')
        yc_curve = yc.ZeroRateCurve(
            self.domain, self.points, origin=self.today, forward_tenor='3M')
        self._rate_curve_test(dcf_curve, yc_curve, places=2)

    def test_cash_rate_curve(self):
        dcf_curve = dcf.CashRateCurve(
            self.domain, self.points, origin=self.today, forward_tenor='3M')
        yc_curve = yc.CashRateCurve(
            self.domain, self.points, origin=self.today, forward_tenor='3M')

        self._rate_curve_test(dcf_curve, yc_curve, places=3)

    def test_short_rate_curve(self):
        dcf_curve = dcf.ShortRateCurve(
            self.domain, self.points, origin=self.today, forward_tenor='3M')
        dcf_curve._TIME_SHIFT = '6m'
        yc_curve = yc.ShortRateCurve(
            self.domain, self.points, origin=self.today, forward_tenor='3M')

        self._rate_curve_test(dcf_curve, yc_curve, places=2)
