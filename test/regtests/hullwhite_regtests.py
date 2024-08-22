from regtest import RegressionTestCase

from yieldcurves.models import NelsonSiegelSvensson, HullWhite
from yieldcurves.tools import lin


class HullWhiteRegTests(RegressionTestCase):

    def setUp(self):
        params = {
                'beta0': 1.0138959988,
                'beta1': 1.836312606,
                'beta2': 2.9874138836,
                'beta3': 4.8105550065,
                'tau1': 0.7389058665,
                'tau2': 12.0362372437
            }
        self.curve = NelsonSiegelSvensson(**params)

    def test_spot_rate(self):
        hw = HullWhite(mean_reversion=0.1, volatility=0.05).curve(self.curve)
        hw.model.random.seed(101)
        self.assertRegressiveEqual(str(hw.model))
        self.assertRegressiveEqual(str(hw))

        for _ in range(10):
            for t in lin(0., 10., 0.25):
                self.assertAlmostRegressiveEqual(hw(t))
                for k, v in hw.items():
                    self.assertAlmostRegressiveEqual(k)
                    self.assertAlmostRegressiveEqual(v)
            hw.evolve()

    def test_foreign_spot_rate(self):
        domestic = \
            HullWhite(mean_reversion=0.1, volatility=0.05).curve(self.curve)
        domestic.model.random.seed(101)
        foreign = HullWhite(mean_reversion=0.1, volatility=0.05,
                            fx_volatility=0.2, domestic=domestic.model,
                            domestic_correlation=0.6, fx_correlation=0.2,
                            domestic_fx_correlation=0.1).curve(self.curve)
        fx = foreign.model.fx(2.5)

        for _ in range(10):
            self.assertAlmostRegressiveEqual(float(fx))
            for t in lin(0., 10., 0.25):
                self.assertAlmostRegressiveEqual(domestic(t))
                self.assertAlmostRegressiveEqual(foreign(t))
            q = domestic.model.q()
            domestic.evolve(q=q[0])
            foreign.evolve(q=q[1])
            fx.evolve(q=q)

    def test_foreign_fx_curve(self):
        domestic = \
            HullWhite(mean_reversion=0.1, volatility=0.05).curve(self.curve)
        domestic.model.random.seed(101)
        foreign = HullWhite(mean_reversion=0.1, volatility=0.05,
                            fx_volatility=0.2, domestic=domestic.model,
                            domestic_correlation=0.6, fx_correlation=0.2,
                            domestic_fx_correlation=0.1).curve(self.curve)
        fx = foreign.model.fx(
            2., domestic_curve=domestic, foreign_curve=foreign)

        for _ in range(10):
            self.assertAlmostRegressiveEqual(float(fx))
            for t in lin(0., 10., 0.25):
                self.assertAlmostRegressiveEqual(fx(t))
                self.assertAlmostRegressiveEqual(domestic(t))
                self.assertAlmostRegressiveEqual(foreign(t))
            q = domestic.model.q()
            domestic.evolve(q=q[0])
            foreign.evolve(q=q[1])
            fx.evolve(q=q)

    def test_foreign_fx_exceptions(self):
        domestic = HullWhite(0.1, 0.05).curve(self.curve)
        foreign = HullWhite(0.2, 0.1, fx_volatility=0.2,
                            domestic=domestic.model).curve(self.curve)
        self.assertRaises(ValueError, HullWhite.Fx, 1.,
                          model=domestic.model, domestic_curve=domestic,
                          foreign_curve=foreign)
        self.assertRaises(ValueError, HullWhite.Fx, 1.,
                          model=foreign.model, domestic_curve=foreign,
                          foreign_curve=foreign)
        self.assertRaises(ValueError, HullWhite.Fx, 1.,
                          model=foreign.model, domestic_curve=domestic,
                          foreign_curve=domestic)


    def test_global_exceptions(self):
        rate_corr = [
            [1.0, 0.6, 0.8],
            [0.6, 1.0, 0.7],
            [0.8, 0.7, 1.0]
        ]
        fx_corr = [
            [1.0, 0.3],
            [0.3, 1.0]
        ]
        rate_fx_corr = [
            [0.11, 0.12],
            [0.21, 0.22],
            [0.31, 0.32]
        ]
        corr = HullWhite.Global.foreign_correlation(
            rate_corr, fx_corr, rate_fx_corr)

        domestic = HullWhite(0.1, 0.04).curve(0.01)
        factors = HullWhite.Global.foreign_factors(
            [0.02, 0.03], fx=[1.2, 2.3],
            mean_reversion=[0.12, 0.21], volatility=[0.06, 0.07],
            domestic=domestic, fx_volatility=[0.1, 0.2])
        # error testing
        # HullWhite.Global(factors)
        self.assertRaises(ValueError, HullWhite.Global, factors)
        # HullWhite.Global([domestic] + 2* factors, corr)
        self.assertRaises(
            ValueError, HullWhite.Global, [domestic] + 2 * factors, corr)

    def test_global_simulation(self):
        rate_corr = [
            [1.0, 0.6, 0.8],
            [0.6, 1.0, 0.7],
            [0.8, 0.7, 1.0]
        ]
        fx_corr = [
            [1.0, 0.3],
            [0.3, 1.0]
        ]
        rate_fx_corr = [
            [0.11, 0.12],
            [0.21, 0.22],
            [0.31, 0.32]
        ]
        corr = HullWhite.Global.foreign_correlation(
            rate_corr, fx_corr, rate_fx_corr)

        self.assertEqual(5, len(corr))

        domestic = HullWhite(0.1, 0.04).curve(0.01)
        factors = HullWhite.Global.foreign_factors(
            [0.02, 0.03], fx=[1.2, 2.3],
            mean_reversion=[0.12, 0.21], volatility=[0.06, 0.07],
            domestic=domestic, fx_volatility=[0.1, 0.2])

        self.assertEqual(4, len(factors))

        g = HullWhite.Global([domestic] + factors, correlation=corr)

        self.assertAlmostRegressiveEqual(g.correlation)
        for f in g.factors:
            self.assertAlmostRegressiveEqual(f)

        for _ in range(4):
            for f in g.factors:
                for k, v in f.items():
                    self.assertAlmostRegressiveEqual(k)
                    self.assertAlmostRegressiveEqual(v)
            g.evolve(.75)

        g.clear()
        for f in g.factors:
            self.assertEqual(0, len(f.keys()))

        domestic = HullWhite(0.1, 0.04).curve(0.001)
        g = HullWhite.Global.from_parameters(
            [0.02, 0.03], fx=[1.2, 2.3],
            mean_reversion=[0.12, 0.21], volatility=[0.06, 0.07],
            domestic=domestic, fx_volatility=[0.1, 0.2], correlation=corr)

        for _ in range(4):
            for f in g.factors:
                for k, v in f.items():
                    self.assertAlmostRegressiveEqual(k)
                    self.assertAlmostRegressiveEqual(v)
            g.evolve(.75)

        g.clear()
        for f in g.factors:
            self.assertEqual(0, len(f.keys()))
