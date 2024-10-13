from regtest import RegressionTestCase

from curves import Curve


class AlgebraRegTests(RegressionTestCase):

    def test_copy(self):
        X = Curve()
        self.assertTrue(X == X)
        self.assertTrue(X == X.__copy__())
        self.assertFalse(X is X.__copy__())
        self.assertTrue(X.__copy__() == X.__copy__())
        self.assertFalse(X.__copy__() is X.__copy__())

    def test_inverse(self):
        X = Curve()
        str_x = str(X)
        X += 1
        X -= 1
        self.assertEqual(str_x, str(X))
        X *= 3
        X /= 3
        self.assertEqual(str_x, str(X))
