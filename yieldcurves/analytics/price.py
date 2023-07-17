
from ..compounding import continuous_rate
from ..tools.adapter import CurveAdapter, init_curve
from .rate import CompoundingFactor


class PriceAdapter(CurveAdapter):
    """domestic price of (optional foreign) assets from spot price and fx"""

    def __init__(self, curve, spot=1.0, fx=1.0, foreign=0.0,
                 *, invisible=None):
        curve = init_curve(curve, curve_type=CompoundingFactor)
        super().__init__(init_curve(curve), invisible=invisible)
        self.spot = init_curve(spot)
        self.fx = init_curve(fx)
        self.foreign = init_curve(foreign, curve_type=CompoundingFactor)

    def __call__(self, x):
        """price at time **x**

        :param x: time to maturity
        """
        z = x
        y = max(min(z, z, *self.spot), z, *self.spot)
        x = max(min(z, z, *self.fx), z, *self.fx)

        fx = self.fx(x) * self.foreign(x, z) / self.curve(x, z)  # fx at z
        s = self.spot(y) * self.foreign(y, z)  # price at z in foreign
        return s * fx / self.curve(z)  # price at zero


class PriceYieldAdapter(CurveAdapter):
    """domestic price yield of (opt. foreign) assets from spot price and fx"""
    def __init__(self, curve, spot=1.0, fx=1.0, foreign=0.0,
                 *, invisible=None):
        curve = PriceAdapter(
            curve, spot=spot, fx=fx, foreign=foreign, invisible=invisible)
        super().__init__(curve, invisible=invisible)

    def __call__(self, x, y=None):
        """yield of relativ asset price change between **x** and **y**

        :param x: time of spot price
        :param y: time to maturity (optional, default is **None**,
            then **x** is time to maturity and spot time will be 0.0)
        :return: yield at maturity starting at spot **x**
        """
        if y is None:
            return self.curve(x)
        f = self.curve(y) / self.curve(x)
        return continuous_rate(f, y - x)
