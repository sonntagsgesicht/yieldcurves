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

from yieldcurves import NelsonSiegelSvensson
from yieldcurves.interpolation import constant
from yieldcurves.analytics.rate import ZeroZ, from_zero, ZeroRateAdapter, \
    Df, from_df, DiscountFactorAdapter, from_cash, CashRateAdapter, \
    from_short, ShortRateAdapter
from yieldcurves.curve import init_curve


def lin(start, stop, step):
    r = [start]
    while r[-1] + step < stop:
        r.append(r[-1] + step)
    return r


class IdentityUnitTests(TestCase):
    def setUp(self):
        x_list = lin(0.01, 2.9, 0.2)
        y_list = [0.017, 0.016, 0.015, 0.0155, 0.0165] * len(x_list)
        self.constant_curve = init_curve(0.02)
        self.constant_interploation_curve = \
            init_curve(constant(x_list, y_list[:len(x_list)]))
        self.curve = init_curve(NelsonSiegelSvensson().download())
        self.grid = lin(0.01, 3.0, 0.8)
        self.places = 7
        self.curve = self.constant_curve

    def x_test(self, origin, transform, places=13):
        for x in self.grid:
            a = origin(x)
            b = transform(x)
            self.assertAlmostEqual(a, b, places=places, msg=f'at {x}')

    def xy_test(self, origin, transform, places=13):
        for x in self.grid:
            for y in self.grid:
                if x == y:
                    continue
                a = origin(x, y)
                b = transform(x, y)
                self.assertAlmostEqual(a, b, places=places, msg=f'at {x} {y}')


class RateIdentityUnitTests(IdentityUnitTests):

    def dzsc_test(self, adapter, df, zero, short, cash):
        self.x_test(df, adapter.df)
        self.xy_test(df, adapter.df)

        self.x_test(zero, adapter.zero)
        self.xy_test(zero, adapter.zero)

        self.x_test(short, adapter.short)
        # self.xy_test(short, adapter.short)

        # self.x_test(cash, adapter.cash)
        self.xy_test(cash, adapter.cash)

    def test_zero_adapter(self):
        # constant
        curve = self.constant_curve
        self.dzsc_test(ZeroRateAdapter(curve), *from_zero(curve))

        # linear interpolated
        curve = self.constant_interploation_curve
        self.dzsc_test(ZeroRateAdapter(curve), *from_zero(curve))

        # curve
        curve = self.curve
        self.dzsc_test(ZeroRateAdapter(curve), *from_zero(curve))

    def test_df_adapter(self):
        # constant
        curve = self.constant_curve
        curve = Df(ZeroZ(curve))
        self.dzsc_test(DiscountFactorAdapter(curve), *from_df(curve))

        # linear interpolated
        curve = self.constant_interploation_curve
        curve = Df(ZeroZ(curve))
        self.dzsc_test(DiscountFactorAdapter(curve), *from_df(curve))

        # curve
        curve = self.curve
        curve = Df(ZeroZ(curve))
        self.dzsc_test(DiscountFactorAdapter(curve), *from_df(curve))

    def test_short_adapter(self):
        # constant
        curve = self.constant_curve
        self.dzsc_test(ShortRateAdapter(curve), *from_short(curve))

        # linear interpolated
        curve = self.constant_interploation_curve
        self.dzsc_test(ShortRateAdapter(curve), *from_short(curve))

        # curve
        curve = self.curve
        self.dzsc_test(ShortRateAdapter(curve), *from_short(curve))

    def test_cash_adapter(self):
        # constant
        curve = self.constant_curve
        self.dzsc_test(CashRateAdapter(curve, 0.25), *from_cash(curve, 0.25))

        # linear interpolated
        curve = self.constant_interploation_curve
        self.dzsc_test(CashRateAdapter(curve, 0.25), *from_cash(curve, 0.25))

        # curve
        curve = self.curve
        self.dzsc_test(CashRateAdapter(curve, 0.25), *from_cash(curve, 0.25))


# class PriceIdentityUnitTests(IdentityUnitTests):
#
#     def test_price_yield(self):
#         origin = Cv(self.curve)
#         transform = Yield(Price(origin))
#         self.x_test(self.curve, transform)
#
#
# class CreditIdentityUnitTests(IdentityUnitTests):
#
#     def test_pd_prob(self):
#         origin = Prob(self.curve)
#         transform = ProbPd(Pd(origin))
#         self.x_test(origin, transform)
#         self.xy_test(origin, transform)
#
#     def test_intensity_prob(self):
#         origin = IntensityI(self.curve)
#         transform = Intensity(Prob(origin))
#         self.x_test(origin, transform)
#         self.xy_test(origin, transform)
#
#     def test_intensity_hz(self):
#         origin = IntensityI(self.curve)
#         transform = IntensityHz(HazardRate(origin))
#         self.x_test(origin, transform)
#         # self.xy_test(origin, transform)
#
#     def test_marginal_prob(self):
#         origin = Prob(self.curve)
#         transform = ProbM(Marginal(origin))
#         # measure error in intensity
#         origin = Intensity(origin)
#         transform = Intensity(transform)
#         self.x_test(origin, transform)
#         # self.xy_test(origin, transform)
