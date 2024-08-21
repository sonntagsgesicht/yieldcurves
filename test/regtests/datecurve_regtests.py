from regtest import RegressionTestCase

from businessdate import BusinessDate
from businessdate import daycount as dcc

from yieldcurves.datecurves import DateCurve
from yieldcurves.tools import lin, AlgebraCurve


day_count = DateCurve.dyf
DAYS_IN_YEAR = DateCurve.DAYS_IN_YEAR


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
            curve = AlgebraCurve()
            a = DateCurve(curve, origin=today, yf=day_count)
            for y in lin(0, 11.1, 0.123456):
                self.assertRegressiveEqual(str(a.inverse(y)))
