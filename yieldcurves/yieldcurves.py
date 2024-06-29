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
class YieldCurveAdapter:

    def __init__(self, curve, *, spot_price=None,
                 frequency=None, cash_frequency=None, swap_frequency=None):
        """

        :param curve: curve of yields
        :param frequency: compounding frequency
            * None -> contintous compounding
            * 0 -> simple compounding
            * 12 -> monthly compounding
            * 4 -> quarterly compounding
            * 2 -> semi annually compounding
            * 4 -> annually compounding
            (optional, default: None)
        :param cash_frequency: cash rate compounding frequency
            (optional, default: 4)
        :param forward_curve: forward cash rate curve
            for swap par rate calculation.
            If no **forward_curve** given, this curve it self will be used.
            (optional, default: self)
        :param kind: key to set different **curve** types.
            Possible types are
            * **price**, see |YieldCurve.from_prices()|
            * **spot**, see |YieldCurve.from_spot_rates()|
            * **zero**, see |YieldCurve.from_zero_rates()|
            * **cash**, see |YieldCurve.from_cash_rates()|
            * **swap**, see |YieldCurve.from_swap_rates()| or
            * **prob**, see |YieldCurve.from_prob_rates()|.
            (optional: default: None, i.e. **spot**)

        """
        self.curve = curve if callable(curve) else _const(curve)
        self.spot_price = spot_price  # spot price at time 0
        self.frequency = frequency  # compounding frequency of spot rate
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
        if y is None:
            spot_price = 1 if self.spot_price is None else self.spot_price
            return spot_price / continuous_compounding(self(x), x)
        return self.price(y) / self.price(x)

    def spot(self, x, y=None):
        if y is None:
            x, y = 0, x
        df = self.price(x) / self.price(y)
        return continuous_rate(df, y - x)

    def short(self, x):
        try:
            y = min((d for d in self if x < d), default=x + EPS)
            x = max((d for d in self if d <= x), default=x)
        except TypeError:
            x, y = x - EPS / 2, x + EPS / 2
        return self.spot(x, y)

    # --- interest rate methods ---

    def df(self, x, y=None):
        if y is None:
            x, y = 0, x
        return self.price(x) / self.price(y)

    def zero(self, x, y=None):
        frequency = self.frequency or getattr(self.curve, 'frequency', None)
        if y is None:
            x, y = 0, x
        df = self.df(x, y)
        if frequency:
            return periodic_rate(df, y - x, frequency)
        return continuous_rate(df, y - x)

    def cash(self, x, y=None):
        if y is None:
            frequency = self.cash_frequency or \
                        getattr(self.curve, 'cash_frequency', None) or \
                        CASH_FREQUENCY
            y = x + 1 / float(frequency)
        df = self.df(x, y)
        return simple_rate(df, y - x)

    def annuity(self, x, y=None):
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
        if isinstance(x, ITERABLE):
            df = self.df(x[0], x[-1])
        else:
            df = self.df(x, y)
        return (1. - df) / self.annuity(x, y)

    # --- credit probs methods ---

    def prob(self, x, y=None):
        if y is None:
            x, y = 0, x
        return self.price(x) / self.price(y)

    def intensity(self, x, y=None):
        return self.spot(x, y)

    def hz(self, x):
        return self.short(x)

    def pd(self, x, y=None):
        return 1 - self.prob(x, y)

    def marginal(self, x):
        return self.prob(x, x + 1)

    def marginal_pd(self, x):
        return 1 - self.prob(x, x + 1)


class CompoundingYieldCurveAdapter(YieldCurveAdapter):
    def __init__(self, curve, *,
                 spot_price=None, frequency=None, cash_frequency=None,
                 compounding_frequency=None):
        super().__init__(curve, spot_price=spot_price,
                         frequency=frequency, cash_frequency=cash_frequency)
        self.compounding_frequency = compounding_frequency


class YieldCurve(YieldCurveAdapter):
    class from_prices(YieldCurveAdapter):
        def __call__(self, x):
            return continuous_rate(self.curve(0) / self.curve(x), x)

    class from_spot_rates(YieldCurveAdapter):
        pass

    class from_short_rates(YieldCurveAdapter):
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

    class from_df(YieldCurveAdapter):
        def __call__(self, x):
            return continuous_rate(self.curve(x) / self.curve(0), x)

    class from_zero_rates(CompoundingYieldCurveAdapter):
        def __call__(self, x):
            if x == 0:
                return self.curve(x)
            frequency = self.compounding_frequency
            if frequency is None:
                return self.curve(x)
            if frequency == 0:
                df = simple_compounding(self.curve(x), x)
                return continuous_rate(df, x)
            df = periodic_compounding(self.curve(x), x, frequency)
            return continuous_rate(df, x)

    class from_cash_rates(CompoundingYieldCurveAdapter):
        def __call__(self, x):
            if self.compounding_frequency == 0:
                f = simple_compounding(self.curve(x), x)
                return continuous_rate(f, x)

            tenor = 1 / (self.compounding_frequency or CASH_FREQUENCY)
            n = int(x / tenor)
            f = prod(simple_compounding(self.curve(i * tenor), tenor)
                     for i in range(n))
            f *= simple_compounding(self.curve(n), x - n * tenor)
            return continuous_rate(f, x)

    class from_swap_rates(CompoundingYieldCurveAdapter):

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

            inner = YieldCurve(None, swap_frequency=self.compounding_frequency)
            inner = fit(inner, x_list, y_list, method='swap', precision=1e-7)
            setattr(self, '_fit', (x_list, y_list, inner))
            return inner(x)

    # --- credit probs methods ---

    class from_probs(YieldCurveAdapter):
        def __call__(self, x):
            return continuous_rate(self.curve(x) / self.curve(0), x)

    class from_intensities(YieldCurveAdapter):
        pass

    class from_hazard_rates(YieldCurveAdapter):
        def __call__(self, x):
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                r = integrate(self.curve, 0, x)[0] / x
            return r

    class from_pd(YieldCurveAdapter):
        def __call__(self, x):
            f = (1 - self.curve(x)) / (1 - self.curve(0))
            return continuous_rate(f, x)

    class from_marginal_probs(YieldCurveAdapter):
        def __call__(self, x):
            n = int(x)
            r = sum(continuous_rate(self.curve(i), 1) for i in range(n))
            r += continuous_rate(self.curve(n), 1) * (x - n)
            return r / x

    class from_marginal_pd(YieldCurveAdapter):
        def __call__(self, x):
            n = int(x)
            r = sum(continuous_rate(1 - self.curve(i), 1) for i in range(n))
            r += continuous_rate(1 - self.curve(n), 1) * (x - n)
            return r / x


class YieldCurveOperator:

    def __init__(self, curve: YieldCurve):
        self.curve = curve

    def __call__(self, x, y=None):
        name = snake_case(self.__class__.__name__)
        if hasattr(self.curve, name):
            return getattr(self.curve, name)(x, y)
        msg = f"curve attribute of type {self.__class__.__name__!r} " \
              f"object has no attribute {name!r} that can be called"
        raise AttributeError(msg)

    def __str__(self):
        return f"{self.__class__.__qualname__}({self.curve!s})"

    def __repr__(self):
        return f"{self.__class__.__qualname__}({self.curve!r})"


class Price(YieldCurveOperator): pass  # noqa E701


class Spot(YieldCurveOperator): pass  # noqa E701


class Short(YieldCurveOperator): pass  # noqa E701


# --- interest rate operators ---

class Df(YieldCurveOperator): pass  # noqa E701


class Zero(YieldCurveOperator): pass  # noqa E701


class Cash(YieldCurveOperator): pass  # noqa E701


class Annuity(YieldCurveOperator): pass  # noqa E701


class Swap(YieldCurveOperator): pass  # noqa E701


# --- credit prob operators ---

class Prob(YieldCurveOperator): pass  # noqa E701


class Intensity(YieldCurveOperator): pass  # noqa E701


class Hz(YieldCurveOperator): pass  # noqa E701


class Pd(YieldCurveOperator): pass  # noqa E701


class Marginal(YieldCurveOperator): pass  # noqa E701


class MarginalPd(YieldCurveOperator): pass  # noqa E701
