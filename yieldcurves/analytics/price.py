from ..compounding import continuous_compounding, continuous_rate
from ..curve import curve_wrapper, init_curve, curve_algebra


def price_yield(price, x, y=0.0):
    """yield from forward price curve"""
    return continuous_rate(price(x) / price(y), x - y)


def price_price(curve, spot, x):
    """forward price from spot price and price curve"""
    return curve(x) / curve(0.0) * spot(0.0)


def forward_price(curve, spot, x, y=0.0):
    """forward price from spot price and yield curve"""
    f = 1 / continuous_compounding(curve(x), x)
    if y:
        f /= 1 / continuous_compounding(curve(y), y)
    return f * spot(y)


# --- price curve classes ---

class yield_curve(curve_wrapper):
    """price from yield curve"""

    def __init__(self, curve, spot=1.0, curve_type='yield'):
        spot = init_curve(spot)
        curve = init_curve(curve)
        if curve_type in 'yield_curve':
            self._price = price_price
        elif curve_type in 'price_curve':
            self._price = forward_price
        else:
            raise TypeError(f'no yield curve of type {curve_type}')

        super().__init__(curve, spot=spot)

    def price(self, x):
        return self._price(self.curve, self.spot, x)

    def price_yield(self, x):
        return price_yield(self.price, x)


class fx_curve(yield_curve):
    """forward fx rate from spot rate as well
    domestic and foreign interest rate curve"""

    def __init__(self, spot, domestic=0.0, foreign=0.0, curve_type='fx'):
        domestic = init_curve(domestic)
        foreign = init_curve(foreign)
        curve = curve_algebra(domestic) / foreign
        if curve_type not in 'fx_curve':
            raise TypeError(f'no fx curve of type {curve_type}')
        super().__init__(curve, spot, curve_type='yield')
