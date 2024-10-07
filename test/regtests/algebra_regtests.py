from regtest import RegressionTestCase

from yieldcurves import AlgebraCurve


class AlgebraRegTests(RegressionTestCase):

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
