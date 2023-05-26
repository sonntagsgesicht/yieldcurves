from .compounding import continuous_compounding, continuous_rate


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
