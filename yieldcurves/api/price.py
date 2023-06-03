
from ..curve import DomainCurve
from ..interpolation import constant, linear, loglinearrate
from .wrapper import Yield, Price, Fx


class YieldCurve(DomainCurve):
    """yields from price curve"""

    def __init__(self, domain=(), data=(), interpolation=linear,
                 origin=None, day_count=None, **__):
        super().__init__(domain=domain, origin=origin, day_count=day_count)
        s = DomainCurve.interpolated(domain, data, interpolation, **__)
        self.curve = s.curve

        self.price = self.curve
        self.yields = Yield(self.price)

    def get_forward_price(self, value_date):
        """ asset forward price at **value_date**

        derived by interpolation on given forward prices
        and extrapolation by given discount_factor resp. yield curve

        :param value_date: future date of asset price
        :return: asset forward price at **value_date**
        """
        value_date = self._f(value_date)
        return self.price(value_date)

    def get_price_yield(self, value_date):
        value_date = self._f(value_date)
        return self.yields(value_date)


class PriceCurve(YieldCurve):
    "prices from yield curve and spot price"

    def __init__(self, domain=(), data=(), interpolation=loglinearrate,
                 origin=None, day_count=None, spot=1.0, **__):
        super().__init__(domain=domain, data=data, interpolation=interpolation,
                         origin=origin, day_count=day_count, **__)
        self.spot = spot

        self.yields = self.curve
        self.price = Price(self.yields, spot=self.spot)


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
