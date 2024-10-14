# -*- coding: utf-8 -*-

# yieldcurves
# -----------
# A Python library for financial yield curves.
#
# Author:   sonntagsgesicht
# Version:  0.2.6.1, copyright Monday, 14 October 2024
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


from math import exp, log, pow
from .tools import vectorize


@vectorize(['rate_value', 'maturity_value'], zipped=True)
def simple_compounding(rate_value, maturity_value):
    r"""simple compounded discount factor

    :param rate_value: interest rate $r$
    :param maturity_value: loan maturity $\tau$
    :return: $\frac{1}{1+r\cdot \tau}$
    """
    return 1.0 / (1.0 + rate_value * float(maturity_value))


@vectorize(['rate_value', 'maturity_value'], zipped=True)
def simple_rate(df, period_fraction):
    r"""interest rate from simple compounded dicount factor

    :param df: discount factor $df$
    :param period_fraction: interest rate period $\tau$
    :return: $\frac{1}{df-1}\cdot \frac{1}{\tau}$
    """
    return (1.0 / df - 1.0) / float(period_fraction)


@vectorize(['rate_value', 'maturity_value'], zipped=True)
def continuous_compounding(rate_value, maturity_value):
    r"""continuous compounded discount factor

    :param rate_value: interest rate $r$
    :param maturity_value: loan maturity $\tau$
    :return: $\exp(-r\cdot \tau)$
    """
    return exp(-1.0 * rate_value * float(maturity_value))


@vectorize(['rate_value', 'maturity_value'], zipped=True)
def continuous_rate(df, period_fraction):
    r"""interest rate from continuous compounded dicount factor

    :param df: discount factor $df$
    :param period_fraction: interest rate period $\tau$
    :return: $-\log(df)\cdot \frac{1}{\tau}$
    """
    if not df:
        pass
    return -log(df) / float(period_fraction)


@vectorize(['rate_value', 'maturity_value'], zipped=True)
def periodic_compounding(rate_value, maturity_value, frequency):
    r"""periodically compounded discount factor

    :param rate_value: interest rate $r$
    :param maturity_value: loan maturity $\tau$
    :param frequency: number of interest rate periods $m$
    :return: $(1+\frac{r}{m})^{-\tau\cdot m}$
    """
    if frequency is None:
        return continuous_compounding(rate_value, maturity_value)
    if frequency == 0:
        return simple_compounding(rate_value, maturity_value)

    ex = -frequency * float(maturity_value)
    return pow(1.0 + float(rate_value) / frequency, ex)


@vectorize(['rate_value', 'maturity_value'], zipped=True)
def periodic_rate(df, period_fraction, frequency):
    r"""interest rate from continuous compounded discount factor

    :param df: discount factor $df$
    :param period_fraction: interest rate period $\tau$
    :param frequency: number of interest rate periods $m$
    :return: $(df^{-\frac{1}{\tau\cdot m}}-1) \cdot m$
    """
    period_fraction = float(period_fraction)
    return (pow(df, -1.0 / (period_fraction * frequency)) - 1.0) * frequency


@vectorize(['rate_value', 'maturity_value'], zipped=True)
def annually_compounding(rate_value, maturity_value):
    r"""annually compounded discount factor

    :param rate_value: interest rate $r$
    :param maturity_value: loan maturity $\tau$
    :return: $(1+r)^{-\tau}$
    """
    return periodic_compounding(rate_value, maturity_value, 1)


@vectorize(['rate_value', 'maturity_value'], zipped=True)
def semi_compounding(rate_value, maturity_value):
    r"""semi compounded discount factor

    :param rate_value: interest rate $r$
    :param maturity_value: loan maturity $\tau$
    :return: $(1+\frac{r}{2})^{-\tau\cdot 2}$
    """
    return periodic_compounding(rate_value, maturity_value, 2)


@vectorize(['rate_value', 'maturity_value'], zipped=True)
def quarterly_compounding(rate_value, maturity_value):
    r"""quarterly compounded discount factor

    :param rate_value: interest rate $r$
    :param maturity_value: loan maturity $\tau$
    :return: $(1+\frac{r}{4})^{-\tau\cdot 4}$
    """
    return periodic_compounding(rate_value, maturity_value, 4)


@vectorize(['rate_value', 'maturity_value'], zipped=True)
def monthly_compounding(rate_value, maturity_value):
    r"""monthly compounded discount factor

    :param rate_value: interest rate $r$
    :param maturity_value: loan maturity $\tau$
    :return: $(1+\frac{r}{12})^{-\tau\cdot 12}$
    """
    return periodic_compounding(rate_value, maturity_value, 12)


@vectorize(['rate_value', 'maturity_value'], zipped=True)
def daily_compounding(rate_value, maturity_value):
    r"""daily compounded discount factor

    :param rate_value: interest rate $r$
    :param maturity_value: loan maturity $\tau$
    :return: $(1+\frac{r}{365})^{-\tau\cdot 365}$
    """
    return periodic_compounding(rate_value, maturity_value, 365)


@vectorize(['rate_value', 'maturity_value'], zipped=True)
def compounding_factor(rate_value, maturity_value, frequency=None):
    r"""compounded discount factor

    :param rate_value: interest rate $r$ per year
    :param maturity_value: maturity $\tau$ in years
    :param frequency: number of interest rate periods per year
        as in |periodic_compounding()|
        if **frequency** is **None** |continuous_compounding()| is used
        and if **period_value** is **0** |simple_compounding()| is used.
    :return:
    """
    if frequency is None or frequency < 0:
        return continuous_compounding(rate_value, maturity_value)
    if frequency == 0:
        return simple_compounding(rate_value, maturity_value)
    return periodic_compounding(rate_value, maturity_value, frequency)


@vectorize(['df', 'period_fraction'], zipped=True)
def compounding_rate(df, period_fraction, frequency):
    r"""interest rate from compounded discount factor

    :param df: discount factor $df$
    :param period_fraction: interest rate period $\tau$ in years
    :param frequency: number of interest rate periods $m$ per year
        as in |periodic_rate()|
        if **frequency** is **None** |continuous_rate()| is used
        and if **frequency** is **0** |simple_rate()| is used.
    """
    if frequency is None or frequency < 0:
        return continuous_rate(df, period_fraction)
    if frequency == 0:
        return simple_rate(df, period_fraction)
    return periodic_rate(df, period_fraction, frequency)


def _validate_compounding_pair(rate, factor):
    r, f = rate, factor
    for t in (0.00002737850787, 0.25, 0.5, .9, 1., 2., 5., 10.):
        for i in (0.0, 0.001, 0.001, 0.01, 0.1, 1):
            if not i == r(f(i, t), t) or \
                    not f(r(f(i, t)), t) == f(i, t):
                raise TypeError("compounding must be tuple"
                                " of inverse functions.")
            # todo: check exp(-t*r) <= f(r, t) <= 1/(1+r*t)
