from regtest import RegressionTestCase

from businessdate import BusinessDate
from businessdate import daycount as dcc
from curves import Curve
from curves.plot import lin

from yieldcurves import DateCurve

day_count = DateCurve._dyf


class YearFrachtionInverseUnitTests(RegressionTestCase):

    def test_inverse(self):
        for day_count in dir(dcc):
            if not day_count.startswith('get'):
                continue
            if day_count.startswith('get_act_act_icma'):
                continue
            if day_count.startswith('get_rational_period'):
                continue
            day_count = getattr(dcc, day_count)
            today = BusinessDate(20240630)
            a = DateCurve(Curve(), origin=today, yf=day_count)
            for y in lin(0, 11.1, 0.123456):
                self.assertRegressiveEqual(str(a.inverse(y)))
