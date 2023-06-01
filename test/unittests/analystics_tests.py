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
from yieldcurves.analytics.rate import zero_rate, zero_rate_df
from yieldcurves.interpolation import constant, linear
from yieldcurves.curve import interpolation_builder, generate_call_wrapper, \
    init_curve


def lin(start, stop, step):
    r = [start]
    while r[-1] + step < stop:
        r.append(r[-1] + step)
    return r


df = generate_call_wrapper('df')
zero = generate_call_wrapper('zero')
cash = generate_call_wrapper('cash')
short = generate_call_wrapper('short')


class AnalyticsUnitTests(TestCase):
    def setUp(self):
        self.today = 1.0
        x_list = [0.25 * x for x in range(8)]
        y_list = [0.01, 0.015, 0.02, 0.018] * 2
        self.lin_curve = interpolation_builder(x_list, y_list, linear)

    def test_zero_rate(self):
        for d in self.lin_curve:
            ds = init_curve(zero_rate_df(self.lin_curve, d))
            zs = zero_rate(ds, d)

    def test_rate_curve(self):
        zero_curve = rate_curve(self.lin_curve, frequency=4, curve_type='zero')
        for d in lin(0.001, 8.0, 0.1):
            self.assertAlmostEqual(zero_curve.zero(d), self.lin_curve(d))

        other_curve = rate_curve(short(zero_curve), frequency=4, curve_type='short')
        for d in lin(0.0, 2.0, 0.1):
            self.assertAlmostEqual(zero_curve.df(d), other_curve.df(d))

        other_curve = rate_curve(cash(zero_curve), frequency=4, curve_type='cash')
        for d in lin(0.0, 2.0, 0.1):
            self.assertAlmostEqual(zero_curve.cash(d), cash(zero_curve)(d))
            self.assertAlmostEqual(zero_curve.cash(d), other_curve.cash(d))
