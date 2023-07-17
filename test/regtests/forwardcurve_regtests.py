
from regtest import RegressionTestCase

from yieldcurves import YieldCurve


class YieldCurveRegTests(RegressionTestCase):

    def setUp(self):
        self.domain = tuple(range(1, 10))
        self.data = tuple(map(lambda x: 1/(100 + x*x), self.domain))
        self.rate = 0.01
        self.spot = self.data[-1]

    def test_forward(self):
        f = YieldCurve(self.domain, self.data)
        for x in range(1, 100):
            self.assertAlmostRegressiveEqual(f(x))
