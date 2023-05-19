from .compounding import continuous_rate, continuous_compounding, \
    simple_rate, simple_compounding, compounding_rate, compounding_factor

EPS = 1/250


def compounding_forwards(curve, x, y=0.0, tenor=None):
    """compound forward rates"""
    # integrate from y to x the discount factor f
    if x == y:
        return 1.0
    if x < y:
        return 1 / compounding_forwards(curve, x, y, tenor=tenor)
    compounding = simple_compounding if tenor else continuous_compounding
    t = tenor or EPS
    f = 1.0
    while y + t < x:
        f *= compounding(curve(y), t)
        y += t
    f *= compounding(curve(y), x - y)
    return f


def discount_factor_df(df_curve, x, y=0.0, compounding_frequency=None):
    """discount factor from discount factor curve"""
    if x == y:
        compounding_frequency += 0  # just to use argument
        return 1.0
    return df_curve(x) / df_curve(y)


def zero_rate(df_curve, x, compounding_frequency=None):
    """zero rate from discount factor curve"""
    return compounding_rate(df_curve(x), x, compounding_frequency)


def zero_rate_df(curve, x, y=0.0, compounding_frequency=None):
    """discount factor from zero rate curve"""
    if x == y:
        return 1.0
    f = compounding_factor(curve(x), x, compounding_frequency)
    if y:
        f /= compounding_factor(curve(y), y, compounding_frequency)
    return f


def cash_rate(df_curve, x, compounding_frequency=4):
    """cash rate from discount factor curve"""
    t = 1 / compounding_frequency
    f = discount_factor_df(df_curve, x + t, x)
    return simple_rate(f, t)


def cash_rate_df(curve, x, y=0.0, compounding_frequency=4):
    """discount factor from cash rate curve"""
    if x == y:
        return 1.0
    t = 1 / compounding_frequency
    return compounding_forwards(curve, x, y, tenor=t)


def short_rate(df_curve, x):
    """short rate from discount factor curve"""
    f = discount_factor_df(df_curve, x + EPS, x)
    return continuous_rate(f, EPS)


def short_rate_df(curve, x, y=0.0, compounding_frequency=None):
    """discount factor from short rate curve"""
    if x == y:
        compounding_frequency += 0  # just to use argument
        return 1.0
    return compounding_forwards(curve, x, y)
