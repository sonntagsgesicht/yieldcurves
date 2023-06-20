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
from yieldcurves.analytics.rate import Cv, Df, Zero, ZeroS, ZeroZ, ZeroC, \
    Cash, CashC, Short
from yieldcurves.analytics.price import Price, Yield
from yieldcurves.analytics.credit import Pd, Prob, ProbPd, ProbM, Marginal, \
    Intensity, IntensityI, IntensityHz, HazardRate
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

    def x_test(self, origin, transform, places=7):
        for x in self.grid:
            a = origin(x)
            b = transform(x)
            self.assertAlmostEqual(a, b, places=places, msg=f'at {x}')

    def xy_test(self, origin, transform, places=7):
        for x in self.grid:
            for y in self.grid:
                a = origin(x, y)
                b = transform(x, y)
                self.assertAlmostEqual(a, b, places=places, msg=f'at {x} {y}')

    def test_zero_df(self):
        # constant
        origin = ZeroZ(self.constant_curve)
        transform = Zero(Df(origin))
        self.x_test(origin, transform)
        self.xy_test(origin, transform)

        # linear interpolated
        origin = ZeroZ(self.constant_interploation_curve)
        transform = Zero(Df(origin))
        self.x_test(origin, transform)
        self.xy_test(origin, transform)

        # curve
        origin = ZeroZ(self.curve)
        transform = Zero(Df(origin))
        self.x_test(origin, transform)
        self.xy_test(origin, transform)

    def test_df_zero(self):
        # constant
        origin = Df(self.constant_curve)
        transform = Df(Zero(origin))
        self.x_test(origin, transform)
        self.xy_test(origin, transform)

        # linear interpolated
        origin = ZeroZ(self.constant_interploation_curve)
        transform = Zero(Df(origin))
        self.x_test(origin, transform)
        self.xy_test(origin, transform)

        # curve
        origin = Df(self.curve)
        transform = Df(Zero(origin))
        self.x_test(origin, transform)
        self.xy_test(origin, transform)

    def test_short_zero(self):
        origin = Cv(self.curve)
        transform = Short(ZeroS(origin))
        self.x_test(self.curve, transform, places=6)

    def test_cash_zero(self):
        origin = Cv(self.curve)
        transform = Cash(ZeroC(origin, frequency=4), frequency=4)
        self.x_test(self.curve, transform)

    def test_zero_cash(self):
        origin = CashC(self.curve)
        transform = ZeroC(Cash(origin, frequency=4), frequency=4)
        self.x_test(self.curve, transform)
        transform = ZeroC(Cash(origin, frequency=2), frequency=2)
        self.x_test(self.curve, transform)
        transform = ZeroC(Cash(origin, frequency=1), frequency=1)
        self.x_test(origin, transform)

    def test_price_yield(self):
        origin = Cv(self.curve)
        transform = Yield(Price(origin))
        self.x_test(self.curve, transform)

    def test_pd_prob(self):
        origin = Prob(self.curve)
        transform = ProbPd(Pd(origin))
        self.x_test(origin, transform)
        self.xy_test(origin, transform)

    def test_intensity_prob(self):
        origin = IntensityI(self.curve)
        transform = Intensity(Prob(origin))
        self.x_test(origin, transform)
        self.xy_test(origin, transform)

    def test_intensity_hz(self):
        origin = IntensityI(self.curve)
        transform = IntensityHz(HazardRate(origin))
        self.x_test(origin, transform, places=4)
        # self.xy_test(origin, transform)

    def test_marginal_prob(self):
        origin = Prob(self.curve)
        transform = ProbM(Marginal(origin))
        # measure error in intensity
        origin = Intensity(origin)
        transform = Intensity(transform)
        self.x_test(origin, transform, places=2)
        # self.xy_test(origin, transform)

