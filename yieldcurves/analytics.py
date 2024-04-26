"""
module to provide
compound rates and factors from curve
rather than from rate values

implements a common signature

    def new_curve(curve, x, y=None, *, **_):
        return

"""
from math import prod

from vectorizeit import vectorize

from .compounding import compounding_factor as _compounding_factor, \
    compounding_rate as _compounding_rate, \
    simple_rate, continuous_compounding, continuous_rate

from .tools import integrate, EPS, ITERABLE


@vectorize(['x', 'y'], zipped=True)
def price_yield(price_curve, x, y=None):
    """return rate / yield from price curve"""
    return compounding_rate(price_curve, x, y)


@vectorize(['x', 'y'], zipped=True)
def price(yield_curve, x, y=None, *, spot=1.0):
    """price from return rate curve / yield curve"""
    if y is None:
        x, y = 0.0, x
    if not callable(spot):
        spot = lambda _: spot
    return spot(x) * compounding_factor(yield_curve, x, y)


@vectorize(['x', 'y'], zipped=True)
def fx_rate(zero_rate_curve, x, y=None, *, spot=1.0, domestic=0.0):
    """fx rate from foreign curve, spot fx rate curve and domestic curve"""
    if y is None:
        x, y = 0.0, x
    if not callable(domestic):
        domestic = lambda _: domestic
    return price(zero_rate_curve, x, y, spot=spot) / price(domestic, x, y)


@vectorize(['x', 'y'], zipped=True)
def compounding_factor(yield_curve, x, y=None, *, frequency=None):
    """discount factor from zero rate curve / yield curve"""
    if x == y:
        return 1.0
    if y is None:
        return _compounding_factor(yield_curve(x), x, frequency)
    fx = _compounding_factor(yield_curve(x), x, frequency)
    fy = _compounding_factor(yield_curve(y), y, frequency)
    return fy / fx


@vectorize(['x', 'y'], zipped=True)
def compounding_rate(discount_factor_curve, x, y=None, *, frequency=None):
    """zero rate / yield from discount factor curve"""
    if y is None:
        return _compounding_rate(discount_factor_curve(x), x, frequency)
    fx = _compounding_factor(discount_factor_curve(x), x, frequency)
    fy = _compounding_factor(discount_factor_curve(y), y, frequency)
    return _compounding_rate(fy / fx, y - x, frequency)


@vectorize(['x', 'y'], zipped=True)
def short_rate(zero_rate_curve, x, y=None, *, eps=EPS):
    """short rate from zero rate curve"""
    if x == y or y is None:
        y = x + eps
    fx = continuous_compounding(zero_rate_curve(x), x)
    fy = continuous_compounding(zero_rate_curve(y), y)
    return continuous_rate(fy / fx, y - x)


@vectorize(['x', 'y'], zipped=True)
def integrated_short_rate(short_rate_curve, x, y=None):
    """zero rate from short rate curve"""
    if y is None:
        x, y = 0.0, x
    if x == y:
        return short_rate_curve(x)
    r = integrate(short_rate_curve, x, y)[0] / (y - x)
    return r


@vectorize(['x', 'y'], zipped=True)
def cash_rate(zero_rate_curve, x, y=None, *, frequency=None):
    """cash rate from zero rate curve"""
    if y is None:
        y = x + 1 / float(frequency)
    fx = _compounding_factor(zero_rate_curve(x), x, frequency)
    fy = _compounding_factor(zero_rate_curve(y), y, frequency)
    return simple_rate(fy / fx, y - x)


@vectorize(['x', 'y'], zipped=True)
def compounded_cash_rate(cash_rate_curve, x, y=None, *, frequency=None):
    """zero rate from cash rate curve"""
    if y is None:
        x, y = 0.0, x
    if x == y:
        return cash_rate_curve(x)
    if x > y:
        return -compounded_cash_rate(cash_rate_curve, y, x, frequency=frequency)
    if not frequency:
        return cash_rate_curve(x)

    # df from compound forward rates
    n = 0
    tenor = 1 / frequency
    while x + (n + 1) * tenor < y:
        n += 1
    frequency = 0
    f = prod(_compounding_factor(cash_rate_curve(x + i * tenor),
                                tenor, frequency) for i in range(n))
    e = x + n * tenor
    f *= _compounding_factor(cash_rate_curve(e), y - e, frequency)
    return _compounding_rate(f, y - x, frequency=frequency)


@vectorize(['x', 'y'], zipped=True)
def swap_annuity(zero_rate_curve, x, y=None, *, frequency=None):
    """swap annuity from zero rate curve"""
    frequency = frequency or 4
    if not isinstance(x, ITERABLE):
        if y is None:
            x, y = 0.0, x
        if x == y:
            return 1.
        step = 1 / frequency
        date_list = [x]
        while date_list[-1] + step < y:
            date_list.append(date_list[-1] + step)
        date_list.append(y)
        x = date_list
    se = tuple(zip(x[:-1], x[1:]))
    res = sum(compounding_factor(
        zero_rate_curve, x[0], e, frequency=frequency) * (e - s)
              for s, e in se)
    return res


@vectorize(['x', 'y'], zipped=True)
def swap_par_rate(zero_rate_curve, x, y=None, *, frequency=None, forward_curve=None):
    """swap par rate from zero rate curve"""
    if y is None:
        x, y = 0.0, x
    if x == y:
        return 0.0
    if forward_curve:
        print('forward_curve not implemented')
    annuity = swap_annuity(zero_rate_curve, [x, y], frequency=frequency)
    df = swap_annuity(zero_rate_curve, x, y, frequency=frequency)
    return (1. - annuity / (y - x)) / df


@vectorize(['x', 'y'], zipped=True)
def default_prob(prob_curve, x, y=None):
    """default prob from prob curve and visa versa"""
    if y is None:
        return 1. - prob_curve(x)
    return 1. - prob_curve(y) / prob_curve(x)


@vectorize(['x', 'y'], zipped=True)
def marginal_prob(prob_curve, x, y=None):
    """marginal prob from prob curve"""
    if y is None:
        y = x + 1.0
    return prob_curve(y) / prob_curve(x)


@vectorize(['x', 'y'], zipped=True)
def compounding_marginal_prob(marginal_prob_curve, x, y=None):
    """prob from marginal prob curve"""
    if y is None:
        x, y = 0.0, x
    if x == y:
        return marginal_prob_curve(x)
    if x > y:
        return -compounding_marginal_prob(marginal_prob_curve, y, x)

    # prob from compound marginal prob
    n = 0
    step = 1.
    while x + (n + 1) * step < y:
        n += 1
    f = prod(marginal_prob_curve(x + i * step) for i in range(n))
    e = x + n * step
    r = _compounding_rate(marginal_prob_curve(e), step)
    return f * _compounding_factor(r, y - e)


@vectorize(['x', 'y'], zipped=True)
def instantaneous_vol(terminal_vol_curve, x, y=None):
    raise NotImplementedError()


@vectorize(['x', 'y'], zipped=True)
def terminal_vol(vol_curve, x, y=None):
    raise NotImplementedError()
