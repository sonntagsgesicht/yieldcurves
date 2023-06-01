from math import exp

from ..compounding import continuous_rate, continuous_compounding, \
    simple_rate, simple_compounding, compounding_rate, compounding_factor
from ..curve import curve_wrapper, init_curve

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


def discount_factor_df(df_curve, x, y=0.0, frequency=None):
    """discount factor from discount factor curve"""
    if x == y:
        frequency += 0  # just to use argument
        return 1.0
    return df_curve(x) / df_curve(y)


def zero_rate(df_curve, x, y=0.0, frequency=None):
    """zero rate from discount factor curve"""
    f = df_curve(x) / df_curve(y)
    return compounding_rate(f, x - y, frequency)


def zero_rate_df(curve, x, y=0.0, frequency=None):
    """discount factor from zero rate curve"""
    if x == y:
        return 1.0
    f = compounding_factor(curve(x), x, frequency)
    if y:
        f /= compounding_factor(curve(y), y, frequency)
    return f


def cash_rate(df_curve, x, y=0.0, frequency=4):
    """cash rate from discount factor curve"""
    y = y or x + 1 / frequency
    f = discount_factor_df(df_curve, y, x)
    return simple_rate(f, y - x)


def cash_rate_df(curve, x, y=0.0, frequency=4):
    """discount factor from cash rate curve"""
    if x == y:
        return 1.0
    t = 1 / frequency
    return compounding_forwards(curve, x, y, tenor=t)


def short_rate(df_curve, x):
    """short rate from discount factor curve"""
    f = discount_factor_df(df_curve, x + EPS, x)
    return continuous_rate(f, EPS)


def short_rate_df(curve, x, y=0.0, frequency=None):
    """discount factor from short rate curve"""
    if x == y:
        frequency = frequency  # just to use argument
        return 1.0
    return compounding_forwards(curve, x, y)


# --- interest rate curve class ---

class rate_curve(curve_wrapper):

    def __init__(self, curve, frequency=None, curve_type='zero'):
        if curve_type in 'zero_rate':
            self._df = zero_rate_df
        elif curve_type in 'cash_rate':
            self._df = cash_rate_df
        elif curve_type in 'short_rate':
            self._df = short_rate_df
        else:
            raise TypeError(f'no rate curve of type {curve_type}')

        curve = init_curve(curve)
        super().__init__(curve)
        self.frequency = frequency

    def df(self, x, y=0.0):
        return self._df(self.curve, x, y, frequency=self.frequency)

    def rate(self, x, y=0.0):
        return self.zero(x, y)

    def zero(self, x, y=0.0):
        return zero_rate(self.df, x, y, frequency=self.frequency)

    def cash(self, x, y=0.0):
        y = x + 1 / self.frequency if not y else y
        return cash_rate(self.df, y, x)

    def short(self, x):
        return short_rate(self.df, x)


class nelson_siegel_svensson_curve(curve_wrapper):

    def __init__(self, beta0=0.0, beta1=0.0, beta2=0.0, beta3=0.0,
                 tau0=1.0, tau1=1.0):
        self.beta0 = beta0
        self.beta1 = beta1
        self.beta2 = beta2
        self.beta3 = beta3
        self.tau0 = tau0
        self.tau1 = tau1
        super().__init__(0.0)

    def df(self, x, y=0.0):
        return zero_rate_df(self.zero, x, y)

    def zero(self, x, y=0.0):
        if y:
            fx = self.zero(x)
            fy = self.zero(y)
            return (fx - fy) / (x - y)
        tau0, tau1 = self.tau0, self.tau1
        a = (1 - exp(-x / tau0)) / (x / tau0)
        b = a - exp(-x / tau0)
        c = (1 - exp(-x / tau1)) / (x / tau1) - exp(-x / tau1)
        beta = self.beta0, self.beta1, self.beta2, self.beta3
        return sum(b * c for b, c in zip(beta, (1, a, b, c)))

    def short(self, x):
        tau0, tau1 = self.tau0, self.tau1
        a = exp(-x / tau0)
        b = a * x / tau0
        c = exp(-x / tau1) * x / tau1
        beta = self.beta0, self.beta1, self.beta2, self.beta3
        return sum(b * c for b, c in zip(beta, (1, a, b, c)))

    def cash(self, x, y=0.0):
        return cash_rate(self.df, x, y)
