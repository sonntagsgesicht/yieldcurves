
from .. import interpolation as _interpolation
from ..daycount import YearFraction
from ..curve import CurveAdapter
from ..interpolation import constant, linear, loglinearrate
from ..analytics.price import Yield, Price, Fx


class YieldCurve(CurveAdapter):
    """prices and yields from yield curve and spot price"""

    def __init__(self, domain=(), data=(), interpolation=linear,
                 origin=None, day_count=None, yield_curve=0.0, **__):
        domain = tuple(domain)

        # build yf transformer, transform domain and build inner curve
        yf = YearFraction(origin, day_count, domain=domain)
        i_type = getattr(_interpolation, str(interpolation), interpolation)
        super().__init__(i_type(yf(domain), data), pre=yf, **__)

        # save properties
        self.domain = domain
        self.origin = origin
        self.day_count = day_count
        self.interpolation = getattr(i_type, '__name__', str(interpolation))

        self.price = Price(yield_curve, spot=self.curve)
        self.yields = Yield(self.price)

    def get_forward_price(self, value_date):
        """ asset forward price at **value_date**

        derived by interpolation on given forward prices
        and extrapolation by given discount_factor resp. yield curve

        :param value_date: future date of asset price
        :return: asset forward price at **value_date**
        """
        value_date = self._pre(value_date)
        return self.price(value_date)

    def get_price_yield(self, value_date):
        value_date = self._pre(value_date)
        return self.yields(value_date)


class PriceCurve(YieldCurve):
    """prices and yields from price curve"""

    def __init__(self, domain=(), data=(), interpolation=loglinearrate,
                 origin=None, day_count=None, **__):
        super().__init__(domain=domain, data=data, interpolation=interpolation,
                         origin=origin, day_count=day_count, **__)

        self.price = self.curve
        self.yields = Yield(self.price)


class FxCurve(YieldCurve):
    """forward fx rate from spot rate as well
    domestic and foreign interest rate curve"""

    def __init__(self, domain=(), data=(), interpolation=constant,
                 origin=None, day_count=None,
                 domestic=0.0, foreign=0.0, **__):
        super().__init__(domain=domain, data=data, interpolation=interpolation,
                         origin=origin, day_count=day_count, **__)

        self.price = Fx(spot=self.curve, domestic=domestic, foreign=foreign)
        self.yields = Yield(self.price)
