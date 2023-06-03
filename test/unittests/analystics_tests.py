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

from yieldcurves.analytics import NelsonSiegelSvensson as NSS
from yieldcurves.interpolation import constant, linear
from yieldcurves.api.wrapper import Df, Zero, ZeroS, ZeroZ, ZeroC, Cash, \
    CashC, Short
from yieldcurves.api.wrapper import Cv, Price, Yield, Fx
from yieldcurves.api.wrapper import Pd, Prob, ProbPd, ProbM, Marginal, \
    Intensity, IntensityI, IntensityHz, Terminal, HazardRate
from yieldcurves.tools import ascii_plot
from yieldcurves.curve import init_curve, CurveAlgebra


def lin(start, stop, step):
    r = [start]
    while r[-1] + step < stop:
        r.append(r[-1] + step)
    return r


class IdentityUnitTests(TestCase):
    def setUp(self):
        x_list = lin(0.01, 2.9, 0.2)
        y_list = [0.017, 0.016, 0.017, 0.018] * len(x_list)
        self.line = linear(x_list, y_list[:len(x_list)])
        self.curve = init_curve(NSS().download())
        self.grid = lin(0.01, 3.0, 0.1)
        self.places = 7

    def x_test(self, origin, transform):
        for x in self.grid:
            a = origin(x)
            b = transform(x)
            self.assertAlmostEqual(a, b, places=self.places)

    def xy_test(self, origin, transform):
        for x in self.grid:
            for y in self.grid:
                a = origin(x, y)
                b = transform(x, y)
                self.assertAlmostEqual(a, b, places=self.places)

    def test_zero(self):
        origin = ZeroZ(self.curve)
        transform = Zero(Df(origin))
        self.x_test(self.curve, transform)
        self.xy_test(origin, transform)

    def test_df(self):
        origin = Df(self.curve)
        transform = Df(Zero(origin))
        self.x_test(origin, transform)
        self.xy_test(origin, transform)

    def test_short(self):
        self.places = 2
        origin = Cv(self.curve)
        transform = Short(ZeroS(origin))
        self.x_test(self.curve, transform)

    def test_cash(self):
        self.places = 2
        origin = Cv(self.curve)
        transform = Cash(ZeroC(origin))
        self.x_test(self.curve, transform)

    def test_price(self):
        origin = Cv(self.curve)
        transform = Yield(Price(origin))
        self.x_test(self.curve, transform)

    def test_pd(self):
        origin = Prob(self.curve)
        transform = ProbPd(Pd(origin))
        self.x_test(origin, transform)
        self.xy_test(origin, transform)

    def test_intensity(self):
        self.places = 2
        origin = IntensityI(self.curve)
        transform = IntensityHz(HazardRate(origin))
        self.x_test(origin, transform)
        self.xy_test(origin, transform)

    def test_marginal(self):
        self.places = 1
        curve = CurveAlgebra(self.curve)
        origin = Prob(curve)
        transform = ProbM(Marginal(origin))
        ascii_plot(self.grid, origin, transform)
        self.x_test(origin, transform)
        self.xy_test(origin, transform)
