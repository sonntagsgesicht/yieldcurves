# -*- coding: utf-8 -*-

# yieldcurves
# -----------
# A Python library for financial yield curves.
#
# Author:   sonntagsgesicht
# Version:  0.2.6.1, copyright Monday, 14 October 2024
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


from math import prod
import warnings

from .compounding import (simple_rate, simple_compounding, periodic_rate,
                          periodic_compounding, continuous_compounding,
                          continuous_rate)
from . import interpolation as _interpolation
from .interpolation import piecewise_linear, fit
from .tools import ITERABLE
from .tools import prettyclass
from .tools import init, integrate


EPS = 1e-8
CASH_FREQUENCY = 4
SWAP_FREQUENCY = 1


# --- YieldCurveAdapter ---

@prettyclass
class _YieldCurveAdapter:

    @classmethod
    def from_interpolation(cls, domain, values,
                           interpolation='piecewise_linear', *,
                           spot_price=None, compounding_frequency=None,
                           cash_frequency=None, swap_frequency=None):
        interpolation = \
            getattr(_interpolation, str(interpolation), interpolation)
        curve = interpolation(domain, values)
        return cls(curve, spot_price=spot_price,
                   compounding_frequency=compounding_frequency,
                   cash_frequency=cash_frequency,
                   swap_frequency=swap_frequency)

    def __init__(self, curve, *, spot_price=None, compounding_frequency=None,
                 cash_frequency=None, swap_frequency=None):
        self.curve = init(curve)
        self.spot_price = spot_price  # spot price at time 0
        self.compounding_frequency = compounding_frequency  # compounding frequency of spot rate  # noqa
        self.cash_frequency = cash_frequency  # default term of cash rate
        self.swap_frequency = swap_frequency  # default term of swap coupons

    def __call__(self, x):
        """returns continuous compounding spot rate"""
        return self.curve(x)

    def __getattr__(self, item):
        if hasattr(self.curve, item):
            return getattr(self.curve, item)
        msg = f"{self.__class__.__name__!r} object has no attribute {item!r}"
        raise AttributeError(msg)

    # --- price yield methods ---

    def price(self, x, y=None):
        """price at x or price factor from x to y"""
        if y is None:
            spot_price = 1 if self.spot_price is None else self.spot_price
            return float(spot_price) / continuous_compounding(self(x), x)
        return self.price(y) / self.price(x)

    def spot(self, x, y=None):
        """spot rate aka. continuous rate aka. yield"""
        if y is None:
            x, y = 0, x
        df = self.price(x) / self.price(y)
        return continuous_rate(df, y - x)

    def short(self, x, y=None):
        """short rate aka. instantaneous forward rate"""
        try:
            y = min((d for d in self if x < d), default=x + EPS)
            x = max((d for d in self if d <= x), default=x)
        except TypeError:
            x, y = x - EPS / 2, x + EPS / 2
        return self.spot(x, y)

    # --- interest rate methods ---

    def df(self, x, y=None):
        """continuous compounded discount factor, i.e. 1 / price(x, y)"""
        if y is None:
            x, y = 0, x
        return self.price(x) / self.price(y)

    def zero(self, x, y=None):
        """zero coupon bond rate, compounded with **frequency**"""
        frequency = self.compounding_frequency or \
            getattr(self.curve, 'frequency', None)
        if y is None:
            x, y = 0, x
        df = self.df(x, y)
        if frequency:
            return periodic_rate(df, y - x, frequency)
        return continuous_rate(df, y - x)

    def cash(self, x, y=None):
        """simple compound cash rate with tenor **1/cash_frequency**"""
        if y is None:
            frequency = self.cash_frequency or \
                        getattr(self.curve, 'cash_frequency', None) or \
                        CASH_FREQUENCY
            y = x + 1 / float(frequency)
        df = self.df(x, y)
        return simple_rate(df, y - x)

    def annuity(self, x, y=None):
        """swap annuity"""
        if not isinstance(x, ITERABLE):
            if y is None:
                x, y = 0.0, x
            if x == y:
                return 1.
            frequency = self.swap_frequency or \
                getattr(self.curve, 'swap_frequency', SWAP_FREQUENCY)
            step = 1 / float(frequency)
            x = [x]
            while x[-1] + step < y:
                x.append(x[-1] + step)
            x.append(y)
        return sum(self.df(x[0], e) * (e - s) for s, e in zip(x[:-1], x[1:]))

    def swap(self, x, y=None):
        """swap par rate"""
        if isinstance(x, ITERABLE):
            df = self.df(x[0], x[-1])
        else:
            df = self.df(x, y)
        return (1. - df) / self.annuity(x, y)

    # --- credit probs methods ---

    def prob(self, x, y=None):
        """survival probability"""
        if y is None:
            x, y = 0, x
        return self.price(x) / self.price(y)

    def intensity(self, x, y=None):
        """Poisson process intensity"""
        return self.spot(x, y)

    def hz(self, x, y=None):
        """hazard rate"""
        return self.short(x)

    def pd(self, x, y=None):
        """probability of default"""
        return 1 - self.prob(x, y)

    def marginal(self, x, y=None):
        """annual survival probability"""
        return self.prob(x, x + 1)

    def marginal_pd(self, x, y=None):
        """annual probability of default"""
        return 1 - self.prob(x, x + 1)


class _CompoundingYieldCurveAdapter(_YieldCurveAdapter):

    def __init__(self, curve, *, spot_price=None, compounding_frequency=None,
                 cash_frequency=None, swap_frequency=None, frequency=None):
        super().__init__(curve, spot_price=spot_price,
                         compounding_frequency=compounding_frequency,
                         cash_frequency=cash_frequency,
                         swap_frequency=swap_frequency)
        self.frequency = frequency


class YieldCurve(_YieldCurveAdapter):

    r"""general financial yield curve

    :param curve: curve of spot yields
    :param spot_price: price at time 0
        (optional: default 1.0)
    :param compounding_frequency: compounding zero rate frequency

        * None -> continuous compounding
        * 0 -> simple compounding
        * 12 -> monthly compounding
        * 4 -> quarterly compounding
        * 2 -> semi annually compounding
        * 1 -> annually compounding

        (optional, default: None i.e. continuous compouding)

    :param cash_frequency: cash rate compounding frequency
        (optional, default: 4 i.e. quarterly compounding)
    :param swap_frequency: swap coupon frequency
        (optional, default: 1 i.e. annual payment)

    |YieldCurve| class consumes a continuous componding yield curve
    as mandantory argument and provides a varity of methods to derive
    financial figures.

    >>> from yieldcurves.interpolation import linear
    >>> from yieldcurves import YieldCurve

    >>> yc = YieldCurve(linear([0, 10], [0.01, 0.02]), spot_price=100, compounding_frequency=12)
    >>> yc
    YieldCurve(linear([0.0, 10.0], [0.01, 0.02]), spot_price=100, compounding_frequency=12)

    **asset yield** related
    -----------------------

    the forward price $p(t) = p_0 \cdot e^{t \cdot r(t)}$
    of asset with spot price of $p_0$

    >>> yc.price(9)
    118.649074...

    forward prices factor $p(t, t') = \frac{p(t')}{p(t)}$

    >>> f = yc.price(1, 9)
    >>> 100 * f * yc.price(0, 1)
    118.6490749...

    spot rate $r(t) = f(0, t)$

    >>> yc.spot(2)
    0.012000...

    and therefor the same as the inner curve

    >>> yc.curve(2)
    0.012

    forward spot rate $f(t, t') = \frac{r(t') - r(t)}{t' - t}$

    >>> yc.spot(2, 4)
    0.015999...


    short rate or instantanuous forward rate $s(t) = \lim_{t' \to t} f(t, t')$
    s.th. $r(t, t') (t' - t) = \int_t^{t'} s(\tau)\ d \tau$

    >>> yc.short(2)
    0.0139999...

    **interest rate** related
    -------------------------

    discount factor $P(t, t') = p(t, t')^{-1}$

    >>> yc.df(1, 9)
    0.852143...

    >>> 1 / yc.price(1, 9)
    0.852143...

    zero rate $P(0, t) = \prod_{i=1}^{m * t} (1 + r(t) / m)^{m \cdot t}$
    with **compounding_frequency** $m$

    >>> yc.zero(9)
    0.019015...

    forward zero rate

    >>> yc.zero(1, 9)
    0.020016...

    simple compounded cash rate
    $L(t) = \frac{1}{\tau} ( P(t) - P(t + \tau) ) P(t, t + \tau)^{-1}$
    with **cash_frequency** $n$ and tenor $\tau = 1 / n$

    >>> yc.cash(5)
    0.020301...

    swap annuity $A(t) = \sum_{i=1}^{k \cdot t} P(0, \frac{i}{k})$
    mit **swap_frequency** $k$ as fixed coupon frequency

    >>> yc.annuity(10)
    9.124091...

    forward swap annuity
    $A(t, t') = \sum_{i=1}^{k \cdot t'} P(t, t + \frac{i}{k})$
    mit **swap_frequency** $k$ as fixed coupon frequency

    >>> yc.annuity(5, 10)
    4.660460...

    forward swap annuity with list argument $T = (t_0, \dots, t_n)$
    $A(T) = \sum_{i=1}^{n} P(t_0, t_i) \cdot (t_i - t_{i-1})$
    and therefor ignoring **swap_frequency**

    >>> yc.annuity([5, 6, 7, 8, 9, 10])
    4.660460...

    forward swap par rate $c(t) = \frac{1 - P(0, t)}{A(t)}$
    with swap annuity $A(t)$.

    >>> yc.swap(10)
    0.019867...

    >>> yc.swap(5, 10)
    0.025212765324721546

    >>> yc.swap([5, 6, 7, 8, 9, 10])
    0.025212...

    **credit** related
    ------------------

    survival probability $P(t, t') = e^{t \cdot r(t) - t' \cdot r(t'))}

    >>> yc.prob(5, 10)
    0.882496...

    intensity $\lambda(t) = r(t)$

    >>> yc.intensity(5)
    0.015000...

    >>> yc.intensity(5, 10)
    0.025000...

    hazard rate $h(t) = \lim_{t' \to t} \lambda(t, t')$

    >>> yc.hz(5)
    0.020000...

    probability of default $pd(t, t') = 1 - P(t, t')$

    >>> yc.pd(5, 10)
    0.117503...

    >>> 1 - yc.prob(5, 10)
    0.117503...

    marginal or annual survival probability $\Pi(t) = P(t, t + 1)$

    >>> yc.marginal(5)
    0.979218...

    >>> yc.prob(5, 6)
    0.979218...

    marginal or annual probability of default $Pd(t) = 1 - \Pi(t)$

    >>> yc.marginal_pd(5)
    0.0207810...

    >>> 1 - yc.prob(5, 6)
    0.0207810...

    """  # noqa 501

    class from_prices(_YieldCurveAdapter):
        """yield curve from curve of prices

        >>> from yieldcurves.interpolation import linear
        >>> from yieldcurves import YieldCurve

        >>> c = linear([0, 10], [100, 120])
        >>> yc = YieldCurve.from_prices(c)
        >>> yc(5)  # spot rate
        0.01906203596086498

        >>> yc.price(10)
        120.0

        """
        def __call__(self, x):
            return continuous_rate(self.curve(0) / self.curve(x), x)

        def price(self, x, y=None):
            if y is None:
                return self.curve(x)
            return super().price(x, y)

    class from_spot_rates(_YieldCurveAdapter):
        """yield curve from curve of spot rates

        >>> from yieldcurves.interpolation import linear
        >>> from yieldcurves import YieldCurve

        >>> c = linear([0, 10], [0.05, 0.06])
        >>> yc = YieldCurve.from_spot_rates(c)
        >>> yc(5)  # spot rate
        0.055

        >>> yc.spot(7.5)
        0.0574999...

        >>> yc.price(10)
        1.8221188...

        """
        pass

    class from_short_rates(_YieldCurveAdapter):
        """yield curve from curve of short rates

        >>> from yieldcurves.interpolation import linear
        >>> from yieldcurves import YieldCurve

        >>> c = linear([0, 10], [0.05, 0.06])
        >>> yc = YieldCurve.from_short_rates(c)
        >>> yc(5)  # spot rate
        0.052500000000000005

        >>> yc.short(10)
        0.06

        >>> yc.price(10)
        1.7332530178673953

        """
        def __call__(self, x):
            if x == 0:
                return self.curve(0)
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                r = integrate(self.curve, 0, x) / x
            return r

        def short(self, x, y=None):
            return self.curve(x)

    # --- interest rate methods ---

    class from_df(_YieldCurveAdapter):
        """yield curve from curve of discount factors

        >>> from yieldcurves.interpolation import linear
        >>> from yieldcurves import YieldCurve

        >>> c = linear([0, 10], [0.99, 0.9])
        >>> yc = YieldCurve.from_df(c)
        >>> yc(5)  # spot rate
        0.009304003126978563

        >>> yc.df(10)
        0.9

        >>> yc.price(10)
        1.0999999999999999

        """
        def __call__(self, x):
            x = x or 1e-12
            return continuous_rate(self.curve(x) / self.curve(0), x)

        def df(self, x, y=None):
            if y is None:
                return self.curve(x)
            return super().df(x, y)

    class from_zero_rates(_CompoundingYieldCurveAdapter):
        """yield curve from curve of zero coupon bond rates

        >>> from yieldcurves.interpolation import linear
        >>> from yieldcurves import YieldCurve

        >>> c = linear([0, 10], [0.05, 0.06])
        >>> yc = YieldCurve.from_zero_rates(c, frequency=12, compounding_frequency=4)
        >>> yc(5)  # spot rate
        0.054874...

        >>> yc.zero(10)
        0.06

        >>> yc.price(10)
        1.819396...

        """  # noqa E501
        def __call__(self, x):
            if x == 0:
                return self.curve(x)
            frequency = self.frequency
            if frequency is None:
                return self.curve(x)
            if frequency == 0:
                df = simple_compounding(self.curve(x), x)
                return continuous_rate(df, x)
            df = periodic_compounding(self.curve(x), x, frequency)
            return continuous_rate(df, x)

        def zero(self, x, y=None):
            if y is None:
                return self.curve(x)
            return super().zero(x, y)

    class from_cash_rates(_CompoundingYieldCurveAdapter):
        """yield curve from curve of simple compound cash rates"""
        def __call__(self, x):
            if self.frequency == 0:
                f = simple_compounding(self.curve(x), x)
                return continuous_rate(f, x)

            tenor = 1 / (self.frequency or CASH_FREQUENCY)
            n = int(x / tenor)
            f = prod(simple_compounding(self.curve(i * tenor), tenor)
                     for i in range(n))
            f *= simple_compounding(self.curve(n), x - n * tenor)
            return continuous_rate(f, x)

        def cash(self, x, y=None):
            return self.curve(x)

    class from_swap_rates(_CompoundingYieldCurveAdapter):
        """yield curve from curve of swap par rates"""

        def __call__(self, x):
            x_list = 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30
            x_list = tuple(getattr(self.curve, 'x_list', x_list))
            x_list = tuple(getattr(self, 'domain', x_list))
            y_list = tuple(self.curve(_) for _ in x_list)

            # try to re-use cached results
            _x_list, _y_list, _inner = getattr(self, '_fit', [()] * 3)
            if x_list == _x_list:
                if y_list == _y_list:
                    return _inner(x)
                if max(abs(a - b) for a, b in zip(_y_list, y_list)) < EPS:
                    return _inner(x)

            inner = YieldCurve(0.0, swap_frequency=self.frequency)
            r = fit(inner.curve, x_list, inner.swap, y_list, tolerance=EPS)
            inner = piecewise_linear(r.keys(), r.values())

            # cache results for later use
            setattr(self, '_fit', (x_list, y_list, inner))
            return inner(x)

        def swap(self, x, y=None):
            if y is None:
                return self.curve(x)
            return super().swap(x, y)

    # --- credit probs methods ---

    class from_probs(_YieldCurveAdapter):
        """yield curve from curve of survival probabilities"""
        def __call__(self, x):
            return continuous_rate(self.curve(x) / self.curve(0), x)

        def prob(self, x, y=None):
            if y is None:
                return self.curve(x)
            return super().prob(x, y)

    class from_intensities(_YieldCurveAdapter):
        """yield curve from curve of intensities"""
        pass

    class from_hazard_rates(_YieldCurveAdapter):
        """yield curve from curve of hazard rates"""
        def __call__(self, x):
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                r = integrate(self.curve, 0, x) / x
            return r

        def hz(self, x, y=None):
            return self.curve(x)

    class from_pd(_YieldCurveAdapter):
        """yield curve from curve of probabilities of default"""
        def __call__(self, x):
            f = (1 - self.curve(x)) / (1 - self.curve(0))
            return continuous_rate(f, x)

        def pd(self, x, y=None):
            if y is None:
                return self.curve(x)
            return super().pd(x, y)

    class from_marginal_probs(_YieldCurveAdapter):
        """yield curve from curve of annual survival probabilities"""
        def __call__(self, x):
            n = int(x)
            r = sum(continuous_rate(self.curve(i), 1) for i in range(n))
            r += continuous_rate(self.curve(n), 1) * (x - n)
            return r / x

        def marginal(self, x, y=None):
            return self.curve(x)

    class from_marginal_pd(_YieldCurveAdapter):
        """yield curve from curve of annual probabilities of default"""
        def __call__(self, x):
            n = int(x)
            r = sum(continuous_rate(1 - self.curve(i), 1) for i in range(n))
            r += continuous_rate(1 - self.curve(n), 1) * (x - n)
            return r / x

        def marginal_pd(self, x, y=None):
            return self.curve(x)
