from regtest import RegressionTestCase

from yieldcurves.tools import AlgebraCurve, lin


class AlgebraRegTests(RegressionTestCase):

    def test_polynomial(self):
        X = AlgebraCurve() @ float
        p = (2 * X + 9 * X * X - X) / X
        self.assertRegressiveEqual(str(p))
        for x in lin(-10, 10, 0.123):
            self.assertAlmostRegressiveEqual(p(x))
        for x in lin(-10, 10, 0.123):
            self.assertAlmostRegressiveEqual(p(str(x)))

    def test_copy(self):
        X = AlgebraCurve()
        self.assertTrue(X == X)
        self.assertFalse(X == X.__copy__())
        self.assertFalse(X.__copy__() == X.__copy__())

    def test_inverse(self):
        X = AlgebraCurve()
        Y = X + 1 - 1
        self.assertEqual(str(X), str(Y))
        Z = X * 3 / 3
        self.assertEqual(str(X), str(Z))
