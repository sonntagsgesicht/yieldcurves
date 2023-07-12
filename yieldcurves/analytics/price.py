
from ..compounding import continuous_compounding, continuous_rate
from ..tools.curve import CurveAdapter, init_curve


class XccyPriceAdapter(CurveAdapter):

    def price(self, x):
        x, y = max(min(x, *self), *self), x
        if x == y:
            return self.curve(x)
        s = self.curve(x)
        d = self.domestic.df(x, y)
        f = self.foreign.df(x, y)
        p = s * d / f
        return self.domestic.df(x) * p



class YieldCurveAdapter(CurveAdapter):

    def __init__(self, curve, spot=1.0, foreign=0.0,
                 call=None, invisible=None):
        """

        :param curve: domestic yield curve
        :param spot: spot price curve
        :param foreign: foreign yield curve
        :param call:
        :param invisible:
        """
        super().__init__(init_curve(curve), call=call, invisible=invisible)
        self.spot = init_curve(spot)
        self.foreign = init_curve(foreign)

    def price(self, x):
        """price at time **x**

        :param x: time to maturity
        """
        x, y = max(min(x, *self.spot), *self.spot), x
        if x == y:
            return self.spot(x)
        # return self.spot(x) / self.curve.factor(x, y)
        s = self.spot(x)
        d = continuous_compounding(self.curve(x), x)
        f = continuous_compounding(self.curve(y), y)
        return s * d / f

    def return_yield(self, x, y=None):
        """yield of relativ asset price change between **x** and **y**

        :param x: time of spot price
        :param y: time to maturity (optional, default is **None**,
            then **x** is time to maturity and spot time will be 0.0)
        :return: yield at maturity starting at spot **x**
        """
        if y is None:
            return self.curve(x)
        f = self.price(y) / self.price(x)
        return continuous_rate(f, y - x)
