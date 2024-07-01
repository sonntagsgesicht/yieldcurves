# -*- coding: utf-8 -*-

# yieldcurves
# -----------
# A Python library for financial yield curves.
#
# Author:   sonntagsgesicht
# Version:  0.1, copyright Saturday, 22 April 2023
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


from math import prod
import warnings

from .compounding import simple_rate, simple_compounding, periodic_rate, \
    periodic_compounding, continuous_compounding, continuous_rate

from .tools import integrate, ITERABLE, snake_case
from .tools.fit import fit
from .tools.pp import pretty

EPS = 1e-8
CASH_FREQUENCY = 4
SWAP_FREQUENCY = 1


class _const:
    """constant curve"""

    def __init__(self, curve):
        self.curve = curve

    def __call__(self, x):
        return self.curve

    def __str__(self):
        return str(self.curve)

    def __repr__(self):
        return repr(self.curve)


# --- YieldCurveAdapter ---

@pretty
class _YieldCurveAdapter:

    def __init__(self, curve, *, spot_price=None, compounding_frequency=None,
                 cash_frequency=None, swap_frequency=None):
        self.curve = curve if callable(curve) else _const(curve)
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
            return spot_price / continuous_compounding(self(x), x)
        return self.price(y) / self.price(x)

    def spot(self, x, y=None):
        """spot rate aka. continuous rate aka. yield"""
        if y is None:
            x, y = 0, x
        df = self.price(x) / self.price(y)
        return continuous_rate(df, y - x)

    def short(self, x):
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

    def hz(self, x):
        """hazard rate"""
        return self.short(x)

    def pd(self, x, y=None):
        """probability of default"""
        return 1 - self.prob(x, y)

    def marginal(self, x):
        """annual survival probability"""
        return self.prob(x, x + 1)

    def marginal_pd(self, x):
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
    118.64907490217118

    forward prices factor $p(t, t') = \frac{p(t')}{p(t)}$

    >>> f = yc.price(1, 9)
    >>> 100 * f * yc.price(0, 1)
    118.64907490217117

    spot rate $r(t) = f(0, t)$

    >>> yc.spot(2)
    0.01200000000000001

    and therefor the same as the inner curve

    >>> yc.curve(2)
    0.012

    forward spot rate $f(t, t') = \frac{r(t') - r(t)}{t' - t}$

    >>> yc.spot(2, 4)
    0.015999999999999993


    short rate or instantanuous forward rate $s(t) = \lim_{t' \to t} f(t, t')$
    s.th. $r(t, t') (t' - t) = \int_t^{t'} s(\tau)\ d \tau$

    >>> yc.short(2)
    0.013999990142199482

    **interest rate** related
    -------------------------

    discount factor $P(t, t') = p(t, t')^{-1}$

    >>> yc.df(1, 9)
    0.8521437889662112

    >>> 1 / yc.price(1, 9)
    0.8521437889662113

    zero rate $P(0, t) = \prod_{i=1}^{m * t} (1 + r(t) / m)^{m \cdot t}$
    with **compounding_frequency** $m$

    >>> yc.zero(9)
    0.019015049608468004

    forward zero rate

    >>> yc.zero(1, 9)
    0.020016675929784178

    simple compounded cash rate
    $L(t) = \frac{1}{\tau} ( P(t) - P(t + \tau) ) P(t, t + \tau)^{-1}$
    with **cash_frequency** $n$ and tenor $\tau = 1 / n$

    >>> yc.cash(5)
    0.02030134441964293

    swap annuity $A(t) = \sum_{i=1}^{k \cdot t} P(0, \frac{i}{k})$
    mit **swap_frequency** $k$ as fixed coupon frequency

    >>> yc.annuity(10)
    9.124091211338056

    forward swap annuity
    $A(t, t') = \sum_{i=1}^{k \cdot t'} P(t, t + \frac{i}{k})$
    mit **swap_frequency** $k$ as fixed coupon frequency

    >>> yc.annuity(5, 10)
    4.660460520774009

    forward swap annuity with list argument $T = (t_0, \dots, t_n)$
    $A(T) = \sum_{i=1}^{n} P(t_0, t_i) \cdot (t_i - t_{i-1})$
    and therefor ignoring **swap_frequency**

    >>> yc.annuity([5, 6, 7, 8, 9, 10])
    4.660460520774009

    forward swap par rate $c(t) = \frac{1 - P(0, t)}{A(t)}$
    with swap annuity $A(t)$.

    >>> yc.swap(10)
    0.019867101580129304

    >>> yc.swap(5, 10)
    0.025212765324721546

    >>> yc.swap([5, 6, 7, 8, 9, 10])
    0.025212765324721546

    **credit** related
    ------------------

    survival probability $P(t, t') = e^{t \cdot r(t) - t' \cdot r(t'))}

    >>> yc.prob(5, 10)
    0.8824969025845953

    intensity $\lambda(t) = r(t)$

    >>> yc.intensity(5)
    0.015000000000000008

    >>> yc.intensity(5, 10)
    0.025000000000000012

    hazard rate $h(t) = \lim_{t' \to t} \lambda(t, t')$

    >>> yc.hz(5)
    0.020000000002

    probability of default $pd(t, t') = 1 - P(t, t')$

    >>> yc.pd(5, 10)
    0.11750309741540466

    >>> 1 - yc.prob(5, 10)
    0.11750309741540466

    marginal or annual survival probability $\Pi(t) = P(t, t + 1)$

    >>> yc.marginal(5)
    0.9792189645694597

    >>> yc.prob(5, 6)
    0.9792189645694597

    marginal or annual probability of default $Pd(t) = 1 - \Pi(t)$

    >>> yc.marginal_pd(5)
    0.02078103543054033

    >>> 1 - yc.prob(5, 6)
    0.02078103543054033

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

        >>> yc.spot(10)
        0.059999999999999984

        >>> yc.price(10)
        1.8221188003905087

        """
        pass

    class from_short_rates(_YieldCurveAdapter):
        """yield curve from curve of short rates

        >>> from yieldcurves.interpolation import linear
        >>> from yieldcurves import YieldCurve

        >>> c = linear([0, 10], [0.05, 0.06])
        >>> yc = YieldCurve.from_short_rates(c)
        >>> yc(5)  # spot rate
        0.05250000000000001

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
                r = integrate(self.curve, 0, x)[0] / x
            return r

        def short(self, x):
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
        0.054874342141609356

        >>> yc.zero(10)
        0.06

        >>> yc.price(10)
        1.81939673403229

        """
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

        def cash(self, x):
            return self.curve(x)

    class from_swap_rates(_CompoundingYieldCurveAdapter):
        """yield curve from curve of swap par rates"""

        def __call__(self, x):
            x_list = 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30
            x_list = tuple(getattr(self.curve, 'x_list', x_list))
            y_list = tuple(self.curve(_) for _ in x_list)

            _x_list, _y_list, _inner = getattr(self, '_fit', [()] * 3)
            if x_list == _x_list:
                if y_list == _y_list:
                    return _inner(x)
                if max(abs(a - b) for a, b in zip(_y_list, y_list)) < 1e-7:
                    return _inner(x)

            inner = YieldCurve(None, swap_frequency=self.frequency)
            inner = fit(inner, x_list, y_list, method='swap', precision=1e-7)
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
                r = integrate(self.curve, 0, x)[0] / x
            return r

        def hz(self, x):
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

        def marginal(self, x):
            return self.curve(x)

    class from_marginal_pd(_YieldCurveAdapter):
        """yield curve from curve of annual probabilities of default"""
        def __call__(self, x):
            n = int(x)
            r = sum(continuous_rate(1 - self.curve(i), 1) for i in range(n))
            r += continuous_rate(1 - self.curve(n), 1) * (x - n)
            return r / x

        def marginal_pd(self, x):
            return self.curve(x)


class YieldCurveOperator:

    def __init__(self, curve: YieldCurve):
        """Operator turning |YieldCurve| into simple callable

        >>> from yieldcurves import YieldCurve
        >>> from yieldcurves.interpolation import linear
        >>> yc = YieldCurve(linear([0, 10], [0.01, 0.02]), spot_price=10)

        Turn yield curve into general finanical curve like ...

        ... a price curve

        >>> from yieldcurves import Price
        >>> p = Price(yc)

        >>> p(1.234)
        10.139592895598932

        >>> yc.price(1.234) == p(1.234)
        True

        ... a spot rate curve

        >>> from yieldcurves import Spot
        >>> s = Spot(yc)

        >>> s(1.234)
        0.011233999999999886

        >>> yc.spot(1.234) == s(1.234)
        True

        ... a short rate curve

        >>> from yieldcurves import Short
        >>> sh = Short(yc)

        >>> sh(1.234)
        0.012468004483236131

        >>> yc.short(1.234) == sh(1.234)
        True

        ... or into interest rate related curve like ...

        ... a discount factor curve

        >>> from yieldcurves import Df
        >>> df = Df(yc)

        >>> df(1.234)
        0.9862328895216768

        >>> yc.df(1.234) == df(1.234)
        True

        ... a zero rate curve

        >>> from yieldcurves import Zero
        >>> z = Zero(yc)

        >>> z(1.234)
        0.011233999999999886

        >>> yc.zero(1.234) == z(1.234)
        True

        ... a cash rate curve

        >>> from yieldcurves import Cash
        >>> ch = Cash(yc)

        >>> ch(1.234)
        0.012738239885720759

        >>> yc.cash(1.234) == ch(1.234)
        True

        ... a swap annuity curve

        >>> from yieldcurves import Annuity
        >>> an = Annuity(yc)

        >>> an(1.234)
        1.2198387749234412

        >>> yc.annuity(1.234) == an(1.234)
        True

        ... a swap par rate curve

        >>> from yieldcurves import Swap
        >>> sw = Swap(yc)

        >>> sw(1.234)
        0.01128600825071107

        >>> yc.swap(1.234) == sw(1.234)
        True

        ... or into credit related curve like ...

        ... a survival probability curve

        >>> from yieldcurves import Prob
        >>> pb = Prob(yc)

        >>> pb(1.234)
        0.9862328895216768

        >>> yc.prob(1.234) == pb(1.234)
        True

        ... a intensity curve

        >>> from yieldcurves import Intensity
        >>> it = Intensity(yc)

        >>> it(1.234)
        0.011233999999999886

        >>> yc.intensity(1.234) == it(1.234)
        True

        ... a hazard rate curve

        >>> from yieldcurves import Hz
        >>> hz = Hz(yc)

        >>> hz(1.234)
        0.012468004483236131

        >>> yc.hz(1.234) == hz(1.234)
        True

        ... a probalility of default curve

        >>> from yieldcurves import Pd
        >>> pd = Pd(yc)

        >>> pd(1.234)
        0.013767110478323241

        >>> yc.pd(1.234) == pd(1.234)
        True

        ... a marginal/annual survival probalility curve

        >>> from yieldcurves import Marginal
        >>> mg = Marginal(yc)

        >>> mg(1.234)
        0.9866222877257945

        >>> yc.marginal(1.234) == mg(1.234)
        True

        ... a marginal/annual probalility of default curve

        >>> from yieldcurves import MarginalPd
        >>> md = MarginalPd(yc)

        >>> md(1.234)
        0.013377712274205478

        >>> yc.marginal_pd(1.234) == md(1.234)
        True

        """
        self.curve = curve

    def __call__(self, x, y=None):
        name = snake_case(self.__class__.__name__)
        if hasattr(self.curve, name):
            if y is None:
                return getattr(self.curve, name)(x)
            return getattr(self.curve, name)(x, y)
        msg = f"curve attribute of type {self.__class__.__name__!r} " \
              f"object has no attribute {name!r} that can be called"
        raise AttributeError(msg)

    def __str__(self):
        return f"{self.__class__.__qualname__}({self.curve!s})"

    def __repr__(self):
        return f"{self.__class__.__qualname__}({self.curve!r})"


class Price(YieldCurveOperator):
    """price curve from |YieldCurve|"""
    pass


class Spot(YieldCurveOperator):
    """spot rate curve from |YieldCurve|"""
    pass


class Short(YieldCurveOperator):
    """spot rate curve from |YieldCurve|"""
    pass


# --- interest rate operators ---

class Df(YieldCurveOperator):
    """discount factor curve from |YieldCurve|"""
    pass


class Zero(YieldCurveOperator):
    """zero coupon bond rate curve from |YieldCurve|"""
    pass


class Cash(YieldCurveOperator):
    """cash rate curve from |YieldCurve|"""
    pass


class Annuity(YieldCurveOperator):
    """swap annuity curve from |YieldCurve|"""
    pass


class Swap(YieldCurveOperator):
    """swap par rate curve from |YieldCurve|"""
    pass


# --- credit prob operators ---

class Prob(YieldCurveOperator):
    """survival probability curve from |YieldCurve|"""
    pass


class Intensity(YieldCurveOperator):
    """intensity curve from |YieldCurve|"""
    pass


class Hz(YieldCurveOperator):
    """hazard rate curve from |YieldCurve|"""
    pass


class Pd(YieldCurveOperator):
    """probability of default curve from |YieldCurve|"""
    pass


class Marginal(YieldCurveOperator):
    """annual survival probability curve from |YieldCurve|"""
    pass


class MarginalPd(YieldCurveOperator):
    """annual probability of default curve from |YieldCurve|"""
    pass
