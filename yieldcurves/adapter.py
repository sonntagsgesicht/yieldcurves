from typing import Callable, Union

from .analytics import price, price_yield, forward_rate, compounding_rate, \
    compounding_factor, cash_rate, short_rate, marginal_prob, default_prob, \
    fx_rate, swap_annuity, swap_par_rate, instantaneous_vol, terminal_vol, EPS

from .tools.fit import fit
from .tools.pp import prepr

class Const:

    def __init__(self, curve: Callable):
        self.curve = curve

    def __call__(self, x):
        return self.curve

    def __str__(self):
        return str(self.curve)

    def __repr__(self):
        return repr(self.curve)


def init(curve: Union[Callable, float]):
    return curve if callable(curve) else Const(curve)


# --- PriceAdapter ---


class PriceAdapter:

    def __init__(self, curve, *, spot=1.0):
        self.curve = init(curve)
        self.spot = spot

    def __str__(self):
        return prepr(self)

    def __repr__(self):
        return prepr(self)

    @property
    def _spot(self):
        return self.spot or \
            getattr(self.curve, 'spot', None) or \
            getattr(self.curve, '_spot', None)

    def price(self, x, y=None):
        return price(self.price_yield, x, y, spot=self._spot)

    def price_yield(self, x, y=None):
        return price_yield(self.price, x, y)


class AssetPrice(PriceAdapter):

    def __call__(self, x, y=None):
        return self.price(x, y)

    def price(self, x, y=None):
        return self.curve(x)


class AssetPriceYield(PriceAdapter):

    def __call__(self, x, y=None):
        return self.price_yield(x, y)

    def price_yield(self, x, y=None):
        if y is None:
            return self.curve(x)
        return forward_rate(self.curve, x, y)


# --- ForeignExchangeRateAdapter ---


class ForeignExchangeRateAdapter:

    def __init__(self, curve, *, spot=None, foreign=None):
        self.curve = init(curve)
        self.spot = spot
        self.foreign = foreign

    def __str__(self):
        return prepr(self)

    def __repr__(self):
        return prepr(self)

    @property
    def _spot(self):
        return self.spot or \
            getattr(self.curve, 'spot', None) or \
            getattr(self.curve, '_spot', None) or \
            1.0

    @property
    def _foreign(self):
        return self.foreign or \
            getattr(self.curve, 'foreign', None) or \
            getattr(self.curve, '_foreign', None) or \
            0.0

    def fx(self, x, y=None):
        return fx_rate(self._foreign, x, y=y,
                       spot=self._spot, domestic=self.curve)


class FxRate(ForeignExchangeRateAdapter):

    def __call__(self, x, y=None):
        return self.fx(x, y)


# --- InterestRateAdapter ---


class InterestRateAdapter:

    def __init__(self, curve, *, frequency=None, cash_frequency=4, eps=EPS,
                 forward_curve=None):
        self.curve = init(curve)
        self.frequency = frequency
        self.cash_frequency = cash_frequency
        self.eps = eps
        self.forward_curve = forward_curve

    def __str__(self):
        return prepr(self)

    def __repr__(self):
        return prepr(self)

    @property
    def _frequency(self):
        return self.frequency or \
            getattr(self.curve, 'frequency', None) or \
            getattr(self.curve, '_frequency', None)

    @property
    def _cash_frequency(self):
        return self.cash_frequency or \
            getattr(self.curve, 'cash_frequency', None) or \
            getattr(self.curve, '_cash_frequency', None) or \
            self.frequency

    @property
    def _eps(self):
        return self.eps or \
            getattr(self.curve, 'eps', None) or \
            getattr(self.curve, '_eps', None)

    @property
    def _forward_curve(self):
        return self.forward_curve or \
            getattr(self.curve, 'forward_curve', None) or \
            getattr(self.curve, '_forward_curve', None)

    def df(self, x, y=None):
        return compounding_factor(self.zero, x, y, frequency=self._frequency)

    def zero(self, x, y=None):
        return compounding_rate(self.df, x, y, frequency=self._frequency)

    def short(self, x, y=None):
        return short_rate(self.zero, x, y, eps=self._eps)

    def cash(self, x, y=None):
        return cash_rate(self.zero, x, y, frequency=self._cash_frequency)

    def annuity(self, x, y=None):
        return swap_annuity(self.zero, x, y,
                            frequency=self._frequency,
                            cash_frequency=self._cash_frequency)

    def par(self, x, y=None):
        return swap_par_rate(self.zero, x, y,
                             frequency=self._frequency,
                             cash_frequency=self._cash_frequency,
                             forward_curve=self._forward_curve)


class ZeroRate(InterestRateAdapter):

    def __call__(self, x, y=None):
        return self.zero(x, y)

    def zero(self, x, y=None):
        if y is None:
            return self.curve(x)
        return forward_rate(self.curve, x, y, frequency=self.frequency)

    def short(self, x, y=None):
        return short_rate(self.curve, x, y)

class DiscountFactor(InterestRateAdapter):

    def __call__(self, x, y=None):
        return self.df(x, y)

    def df(self, x, y=None):
        if y is None:
            return self.curve(x)
        return super().df(x, y)


class ShortRate(InterestRateAdapter):

    def __call__(self, x, y=None):
        return self.short(x, y)

    def short(self, x, y=None):
        if y is None:
            return self.curve(x)
        return super().short(x, y)


class CashRate(InterestRateAdapter):

    def __call__(self, x, y=None):
        return self.cash(x, y)

    def cash(self, x, y=None):
        if y is None:
            return self.curve(x)
        return super().cash(x, y)


class SwapParRate(InterestRateAdapter):

    def __call__(self, x, y=None):
        return self.par(x, y)

    def par(self, x, y=None):
        if y is None:
            return self.curve(x)
        return super().par(x, y)

    def zero(self, x, y=None):
        inner = getattr(self, '_inner', None)
        if inner:
            return inner.zero(x, y)
        x_list = 1, 2, 3, 5, 7, 10, 15, 20, 30
        x_list = getattr(self.curve, 'x_list', x_list)
        y_list = [self.curve(_) for _ in x_list]
        inner = fit(ZeroRate, x_list, y_list, method='par')
        setattr(self, '_inner', inner)
        return inner.zero(x, y)


# --- CreditAdapter ---


class CreditAdapter:

    def __init__(self, curve, *, eps=EPS):
        self.curve = init(curve)
        self.eps = eps

    def __str__(self):
        return prepr(self)

    def __repr__(self):
        return prepr(self)

    @property
    def _eps(self):
        return self.eps or \
            getattr(self.curve, 'eps', None) or \
            getattr(self.curve, '_eps', None)

    def prob(self, x, y=None):
        return compounding_factor(self.intensity, x, y)

    def intensity(self, x, y=None):
        return compounding_rate(self.prob, x, y)

    def hz(self, x, y=None):
        return short_rate(self.intensity, x, y, eps=self._eps)

    def marginal(self, x, y=None):
        return marginal_prob(self.intensity, x, y)

    def pd(self, x, y=None):
        return default_prob(self.intensity, x, y)


class FlatIntensity(CreditAdapter):

    def __call__(self, x, y=None):
        return self.intensity(x, y)

    def intensity(self, x, y=None):
        if y is None:
            return self.curve(x)
        return super().intensity(x, y)


class SurvivalProbability(CreditAdapter):

    def __call__(self, x, y=None):
        return self.prob(x, y)

    def prob(self, x, y=None):
        if y is None:
            return self.curve(x)
        return super().prob(x, y)


class HazardRate(CreditAdapter):

    def __call__(self, x, y=None):
        return self.hz(x, y)

    def hz(self, x, y=None):
        if y is None:
            return self.curve(x)
        return super().hz(x, y)


class MarginalSurvivalProbability(CreditAdapter):

    def __call__(self, x, y=None):
        return self.marginal(x, y)

    def marginal(self, x, y=None):
        if y is None:
            return self.curve(x)
        return super().marginal(x, y)


class DefaultProbability(CreditAdapter):

    def __call__(self, x, y=None):
        return self.pd(x, y)

    def pd(self, x, y=None):
        if y is None:
            return self.curve(x)
        return super().pd(x, y)


# --- VolatilityAdapter ---


class VolatilityAdapter:

    def __init__(self, curve):
        self.curve = init(curve)

    def vol(self, x, y=None):
        return instantaneous_vol(self.curve, x, y)

    def terminal(self, x, y=None):
        return terminal_vol(self.curve, x, y)


class InstantaneousVol(VolatilityAdapter):

    def __call__(self, x, y=None):
        return self.vol(x, y)

    def vol(self, x, y=None):
        if y is None:
            return self.curve(x)
        return super().vol(x, y)


class TerminalVol(VolatilityAdapter):

    def __call__(self, x, y=None):
        return self.terminal(x, y)

    def terminal(self, x, y=None):
        if y is None:
            return self.curve(x)
        return super().terminal(x, y)
