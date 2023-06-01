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

from yieldcurves.analytics import rate_curve
from yieldcurves.analytics.rate import zero_rate, short_rate, cash_rate,\
    zero_rate_df, short_rate_df, cash_rate_df

from yieldcurves.interpolation import constant, linear


def lin(start, stop, step):
    r = [start]
    while r[-1] + step < stop:
        r.append(r[-1] + step)
    return r


class AnalyticsUnitTests(TestCase):
    def setUp(self):
        x_list = lin(0.01, 2.9, 0.2)
        y_list = [0.017, 0.015, 0.02, 0.018] * len(x_list)
        self.xy_list = x_list, y_list[:len(x_list)]
        self.periods = lin(0.01, 3.0, 0.1)
        self.places = 7

    def test_zero_rate_df(self):
        inner = linear(*self.xy_list)
        curve = rate_curve(inner)
        for x in self.periods:
            a = curve.df(x)
            b = zero_rate_df(curve.zero, x)
            self.assertAlmostEqual(a, b, places=self.places)

    def test_short_rate_df(self):
        inner = linear(*self.xy_list)
        curve = rate_curve(inner)
        for x in self.periods:
            a = curve.df(x)
            b = short_rate_df(curve.short, x)
            self.assertAlmostEqual(a, b, places=self.places)

    def test_cash_rate_df(self):
        inner = linear(*self.xy_list)
        curve = rate_curve(inner, frequency=4)
        for x in self.periods:
            a = curve.df(x)
            b = cash_rate_df(curve.cash, x)
            self.assertAlmostEqual(a, b, places=self.places)

    def test_zero_rate(self):
        inner = linear(*self.xy_list)
        curve = rate_curve(inner)
        for x in self.periods:
            a = inner(x)
            b = zero_rate(curve.df, x)
            self.assertAlmostEqual(a, b, places=self.places)

    def test_short_rate(self):
        inner = linear(*self.xy_list)
        curve = rate_curve(inner, curve_type='short')
        for x in self.periods:
            a = inner(x)
            b = short_rate(curve.df, x)
            self.assertAlmostEqual(a, b, places=self.places)

    def test_cash_rate(self):
        inner = linear(*self.xy_list)
        curve = rate_curve(inner, curve_type='cash', frequency=4)
        for x in self.periods:
            a = inner(x)
            b = cash_rate(curve.df, x)
            self.assertAlmostEqual(a, b, places=self.places)
