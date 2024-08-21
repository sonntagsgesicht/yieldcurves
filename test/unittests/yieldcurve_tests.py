from unittest import TestCase

from yieldcurves.tools import lin, AlgebraCurve
from yieldcurves.models import NelsonSiegelSvensson
from yieldcurves.interpolation import linear
from yieldcurves.yieldcurves import YieldCurve


class YieldCurveTests(TestCase):

    def setUp(self):
        self.params = {
            'beta0': 1.0138959988,
            'beta1': 1.836312606,
            'beta2': 2.9874138836,
            'beta3': 4.8105550065,
            'tau1': 0.7389058665,
            'tau2': 12.0362372437
        }
        self.nss = NelsonSiegelSvensson(**self.params)

        days = 1, 2, 7, 14
        month = 1, 3, 6, 9
        years = [1, 2, 3, 4, 5, 7, 10, 15, 20, 25, 30, 40, 50]
        self.domain = [x / 250 for x in days] + [x / 12 for x in month] + years

    def test_curve(self):
        a = self.nss
        b = linear(self.domain, a)
        for x in self.domain:
            self.assertAlmostEqual(a(x), b(x))

        a = AlgebraCurve(self.nss)
        b = YieldCurve(
            a, compounding_frequency=4, cash_frequency=4, swap_frequency=2)
        for x in lin(0.05, 20.05, 0.05):
            self.assertAlmostEqual(a(x), b(x))

        a = AlgebraCurve(0.02)
        b = YieldCurve(
            a, compounding_frequency=4, cash_frequency=4, swap_frequency=2)
        for x in lin(0.05, 20.05, 0.05):
            self.assertAlmostEqual(a(x), b(x))

    def _test_yield_curve(self, f, places=7):
        a = YieldCurve.from_prices(f.price)
        b = YieldCurve.from_short_rates(f.short)
        y = a, b,
        for x in lin(0.05, 20.05, 0.05):
            for g in y:
                self.assertAlmostEqual(f(x), g(x), places=places, msg=g)

    def test_yield_curve(self):
        f = YieldCurve(0.01)
        self._test_yield_curve(f)
        f = YieldCurve(
            0.02, compounding_frequency=4, cash_frequency=4, swap_frequency=2)
        self._test_yield_curve(f)
        f = YieldCurve(self.nss)
        self._test_yield_curve(f)

    def _test_interest_rate_curve(self, f, places=7):
        a = YieldCurve.from_df(f.df)
        b = YieldCurve.from_zero_rates(
            f.zero, frequency=f.compounding_frequency)
        y = a, b,
        for x in lin(0.05, 20.05, 0.05):
            for g in y:
                self.assertAlmostEqual(f(x), g(x), places=places, msg=g)

    def _test_cash_rate_curve(self, f, places=7):
        c = YieldCurve.from_cash_rates(
            f.cash, frequency=f.cash_frequency)
        y = c,
        for x in lin(0.25, 20.05, 0.25):
            for g in y:
                self.assertAlmostEqual(f(x), g(x), places=places, msg=g)

    def _test_swap_rate_curve(self, f, places=7):
        d = YieldCurve.from_swap_rates(
            f.swap, frequency=f.swap_frequency)
        y = d,
        for x in lin(1., 20.05, 1.):
            for g in y:
                self.assertAlmostEqual(f(x), g(x), places=places, msg=g)

    def test_interest_rate_curve(self):
        f = YieldCurve(0.02,
                       compounding_frequency=4,
                       cash_frequency=4,
                       swap_frequency=2)
        self._test_interest_rate_curve(f)
        self._test_cash_rate_curve(f)
        self._test_swap_rate_curve(f, places=5)

        f = YieldCurve(self.nss,
                       compounding_frequency=4,
                       cash_frequency=4,
                       swap_frequency=2)
        self._test_interest_rate_curve(f)
        self._test_cash_rate_curve(f)
        self._test_swap_rate_curve(f, places=3)

    def _test_credit_curve(self, f, places=7):
        a = YieldCurve.from_probs(f.prob)
        b = YieldCurve.from_intensities(f.intensity)
        c = YieldCurve.from_hazard_rates(f.hz)
        d = YieldCurve.from_pd(f.pd)
        y = a, b, c, d
        for x in lin(0.05, 20.05, 0.05):
            for g in y:
                self.assertAlmostEqual(f(x), g(x), places=places, msg=g)

    def _test_marginal_credit_curve(self, f, places=7):
        a = YieldCurve.from_marginal_probs(f.marginal)
        b = YieldCurve.from_marginal_pd(f.marginal_pd)
        y = a, b,
        for x in lin(1, 21, 1):
            for g in y:
                self.assertAlmostEqual(f(x), g(x), places=places, msg=g)

    def test_credit_curve(self):
        f = YieldCurve(0.01)
        self._test_credit_curve(f)
        self._test_marginal_credit_curve(f)

        f = YieldCurve(self.nss)
        self._test_credit_curve(f)
        self._test_marginal_credit_curve(f)
