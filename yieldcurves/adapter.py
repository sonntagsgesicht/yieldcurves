import re

from vectorizeit import vectorize

from .analytics import price, price_yield, compounding_rate, \
    compounding_factor, cash_rate, short_rate, marginal_prob, default_prob, \
    fx_rate, swap_annuity, swap_par_rate, instantaneous_vol, terminal_vol

_p1 = re.compile(r'(.)([A-Z][a-z]+)')
_p2 = re.compile(r'([a-z0-9])([A-Z])')


class _CurveAdapter:

    _call = '__call__'

    def __init__(self, curve):
        self.curve = curve

    def __call__(self, x, y=None):
        return getattr(self.curve, self._call)(x, y)


def _call_adapter(name: str, *classes, attr='') -> type:
    classes += (_CurveAdapter,)
    attr = attr or _p2.sub(r'\1_\2', _p1.sub(r'\1_\2', name)).lower()
    return type(name, classes, {'_call': attr})


# --- PriceAdapter ---


class PriceAdapter:

    def __init__(self, curve, *, spot=1.0):
        self.curve = curve
        self.spot = spot

    def price(self, x, y=None):
        return price(self.price_yield, x, spot=self.spot)

    def price_yield(self, x, y=None):
        return price_yield(self.price, x, y)


Price = _call_adapter('Price', PriceAdapter)
PriceYield = _call_adapter('PriceYield', PriceAdapter)


class AssetPrice(PriceAdapter):

    def price(self, x, y=None):
        return self.curve(x)


class AssetPriceYield(PriceAdapter):

    def price_yield(self, x, y=None):
        if y is None:
            return self.curve(x)
        return super().price_yield(x, y)


class ForeignExchangeRate:

    def __init__(self, curve, *, spot=1.0, foreign=0.0):
        self.curve = curve
        self.spot = spot
        self.foreign = foreign

    def fx(self, x, y=None):
        return fx_rate(self.foreign, x, y=y,
                       spot=self.spot, domestic=self.curve)


Fx = FX = _call_adapter('Fx', ForeignExchangeRate)


# --- InterestRateAdapter ---


class InterestRateAdapter:

    def __init__(self, curve, *, frequency=None, eps=None):
        self.curve = curve
        self.frequency = frequency
        self.eps = eps

    def df(self, x, y=None):
        return compounding_factor(self.zero, x, y, frequency=self.frequency)

    def zero(self, x, y=None):
        return compounding_rate(self.df, x, y, frequency=self.frequency)

    def cash(self, x, y=None):
        return cash_rate(self.zero, x, y, frequency=self.frequency)

    def short(self, x, y=None):
        return short_rate(self.zero, x, y, eps=self.eps)


Zero = _call_adapter('Zero', InterestRateAdapter)
Df = DF = _call_adapter('Df', InterestRateAdapter)
Cash = _call_adapter('Cash', InterestRateAdapter)
Short = _call_adapter('Short', InterestRateAdapter)


class ZeroRate(InterestRateAdapter):

    def zero(self, x, y=None):
        if y is None:
            return self.curve(x)
        return super().zero(x, y)


class DiscountFactor(InterestRateAdapter):

    def df(self, x, y=None):
        if y is None:
            return self.curve(x)
        return super().df(x, y)


class ShortRate(InterestRateAdapter):

    def short(self, x, y=None):
        if y is None:
            return self.curve(x)
        return super().short(x, y)


class CashRate(InterestRateAdapter):

    def cash(self, x, y=None):
        if y is None:
            return self.curve(x)
        return super().cash(x, y)


# --- SwapAdapter ---


class SwapAdapter(InterestRateAdapter):

    def __init__(self, curve, *, frequency=None, eps=None, forward_curve=None):
        super().__init__(curve, frequency=frequency, eps=eps)
        self.forward_curve = forward_curve
        self.frequency = frequency
        self.eps = eps

    def par(self, x, y=None):
        return swap_par_rate(self.zero, x, y,
                             frequency=self.frequency,
                             forward_curve=self.forward_curve)

    def annuity(self, x, y=None):
        return swap_annuity(self.zero, x, y, frequency=self.frequency)


Par = _call_adapter('Par', SwapAdapter)
Annuity = _call_adapter('Annuity', SwapAdapter)


class SwapParRate(SwapAdapter):

    def par(self, x, y=None):
        if y is None:
            return self.curve(x)
        return super().par(x, y)

    def zero(self, x, y=None):
        if y is None:
            raise NotImplementedError()
        return super().zero(x, y)


# --- CreditAdapter ---


class CreditAdapter:

    def __init__(self, curve, *, eps=None):
        self.curve = curve
        self.eps = eps

    def intensity(self, x, y=None):
        return compounding_rate(self.prob, x, y)

    def prob(self, x, y=None):
        return compounding_factor(self.intensity, x, y)

    def hz(self, x, y=None):
        return short_rate(self.intensity, x, y, eps=self.eps)

    def marginal(self, x, y=None):
        return marginal_prob(self.intensity, x, y)

    def pd(self, x, y=None):
        return default_prob(self.intensity, x, y)


Intensity = _call_adapter('Intensity', CreditAdapter)
Prob = _call_adapter('Prob', CreditAdapter)
Hz = HZ = _call_adapter('Hz', CreditAdapter)
Marginal = _call_adapter('Marginal', CreditAdapter)
Pd = PD = _call_adapter('Pd', CreditAdapter)


class FlatIntensity(CreditAdapter):

    def intensity(self, x, y=None):
        if y is None:
            return self.curve(x)
        return super().intensity(x, y)


class SurvivalProbability(CreditAdapter):

    def prob(self, x, y=None):
        if y is None:
            return self.curve(x)
        return super().prob(x, y)


class HazardRate(CreditAdapter):

    def hz(self, x, y=None):
        if y is None:
            return self.curve(x)
        return super().hz(x, y)


class MarginalSurvivalProbability(CreditAdapter):

    def marginal(self, x, y=None):
        if y is None:
            return self.curve(x)
        return super().marginal(x, y)


class DefaultProbability(CreditAdapter):

    def pd(self, x, y=None):
        if y is None:
            return self.curve(x)
        return super().pd(x, y)


# --- VolatilityAdapter ---


class VolatilityAdapter:

    def __init__(self, curve):
        self.curve = curve

    def vol(self, x, y=None):
        return instantaneous_vol(self.curve, x, y)

    def terminal(self, x, y=None):
        return terminal_vol(self.curve, x, y)


Vol = _call_adapter('Vol', VolatilityAdapter)
Terminal = _call_adapter('Terminal', VolatilityAdapter)


class InstantaneousVol(VolatilityAdapter):

    def vol(self, x, y=None):
        if y is None:
            return self.curve(x)
        return super().vol(x, y)


class TerminalVol(VolatilityAdapter):

    def terminal(self, x, y=None):
        if y is None:
            return self.curve(x)
        return super().terminal(x, y)
