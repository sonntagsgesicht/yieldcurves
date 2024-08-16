from regtest import RegressionTestCase

from yieldcurves.models.nelsonsiegel import spot_rate, short_rate, \
    NelsonSiegelSvensson as NSS, NelsonSiegelSvenssonShortRate as NS3


class NelsonSiegelRegTests(RegressionTestCase):

    def setUp(self):
        self.params = [
            {
            },
            {
                'beta0': 1.0138959988,
                'beta1': 1.836312606,
                'beta2': 2.9874138836,
                'beta3': 4.8105550065,
                'tau1': 0.7389058665,
                'tau2': 12.0362372437
            }
        ]

    def test_spot_rate(self):
        for params in self.params:
            for x in range(1, 100):
                self.assertAlmostRegressiveEqual(spot_rate(x, **params))
            x = [0.25, 0.5, 1.0, 1.5, 2.5]
            self.assertAlmostRegressiveEqual(spot_rate(x, **params))

    def test_short_rate(self):
        for params in self.params:
            for x in range(1, 100):
                self.assertAlmostRegressiveEqual(short_rate(x, **params))
            x = [0.25, 0.5, 1.0, 1.5, 2.5]
            self.assertAlmostRegressiveEqual(short_rate(x, **params))

    def test_nelson_siegel_svensson_spot(self):
        for params in self.params:
            f = NSS(**params)
            self.assertRegressiveEqual(str(f))
            for x in range(1, 100):
                self.assertAlmostRegressiveEqual(f(x))
            x = [0.25, 0.5, 1.0, 1.5, 2.5]
            self.assertAlmostRegressiveEqual(f(x))

    def test_nelson_siegel_svensson_short(self):
        for params in self.params:
            f = NS3(**params)
            self.assertRegressiveEqual(str(f))
            for x in range(1, 100):
                self.assertAlmostRegressiveEqual(f(x))
            x = [0.25, 0.5, 1.0, 1.5, 2.5]
            self.assertAlmostRegressiveEqual(f(x))
