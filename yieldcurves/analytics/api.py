from ..tools.adapter import CurveAdapter, init_curve
from .rate import CompoundingRate, CompoundingFactor
from .price import Price, PriceYield
from .interest import CashRate, ShortRate, \
    CompoundingShortRate, CompoundingCashRate
from .credit import CompoundingMarginalProb, DefaultProb


class PriceApiAdapter(CurveAdapter):

    def __init__(self, curve, spot=1.0, fx=1.0, foreign=0.0,
                 *, invisible=None):
        super().__init__(init_curve(curve), invisible=invisible)
        self._price = Price(self.curve, spot, fx, foreign,
                            invisible=True)
        self._yield = PriceYield(self.curve, spot, fx, foreign,
                                 invisible=True)

    def price(self, x):
        return self._price(x)

    def return_yield(self, x, y):
        return self._yield(x, y)


class ZeroRateApiAdapter(CurveAdapter):

    def __init__(self, curve, frequency=None, eps=None, invisible=None):
        super().__init__(init_curve(curve), invisible=invisible)
        self.frequency = frequency
        self.eps = eps
        self.zero = CompoundingRate(self.curve, frequency, invisible=True)
        self.df = CompoundingFactor(self.zero, frequency, invisible=True)
        self.cash = CashRate(self.zero, frequency, invisible=True)
        self.short = ShortRate(self.zero, frequency, eps,
                               invisible=True)


class DiscountFactorApiAdapter(ZeroRateApiAdapter):

    def __init__(self, curve, frequency=None, eps=None, invisible=None):
        curve = CompoundingRate(curve, frequency, invisible=True)
        super().__init__(curve, frequency, eps, invisible=invisible)


class ShortRateApiAdapter(ZeroRateApiAdapter):

    def __init__(self, curve, frequency=None, eps=None, invisible=None):
        curve = CompoundingShortRate(curve, frequency, invisible=True)
        super().__init__(curve, frequency, eps, invisible=invisible)
        self.short = self.curve


class CashRateApiAdapter(ZeroRateApiAdapter):

    def __init__(self, curve, frequency=None, eps=None, invisible=None):
        cash = curve
        curve = CompoundingCashRate(curve, frequency, invisible=True)
        super().__init__(curve, frequency, eps, invisible=invisible)
        self.cash = lambda x, y=None: cash(x)


class CreditApiAdapter(CurveAdapter):

    curve = DiscountFactorApiAdapter(0.0)

    def __init__(self, curve, invisible=None):
        super().__init__(init_curve(curve), invisible=invisible)
        self.prob = self.curve.df
        self.intensity = self.curve.zero
        self.hazard_rate = self.curve.short
        # self.marginal = MarginalProb(self.curve.df, invisible=True)
        # self.pd = DefaultProb(self.curve.df, invisible=True)


class SurvivalProbabilityApiAdapter(CreditApiAdapter):

    def __init__(self, curve, eps=None, invisible=None):
        curve = DiscountFactorApiAdapter(curve, eps=eps, invisible=True)
        super().__init__(curve, invisible=invisible)


class FlatIntensityApiAdapter(CreditApiAdapter):

    def __init__(self, curve, eps=None, invisible=None):
        curve = ZeroRateApiAdapter(curve, eps=eps, invisible=True)
        super().__init__(curve, invisible=invisible)


class HazardRateApiAdapter(CreditApiAdapter):

    def __init__(self, curve, eps=None, invisible=None):
        curve = ShortRateApiAdapter(curve, eps=eps, invisible=True)
        super().__init__(curve, invisible=invisible)


class MarginalSurvivalProbabilityApiAdapter(CreditApiAdapter):

    def __init__(self, curve, eps=None, invisible=None):
        curve = CompoundingMarginalProb(curve, invisible=True)
        curve = DiscountFactorApiAdapter(curve, eps=eps, invisible=True)
        super().__init__(curve, invisible=invisible)


class DefaultProbabilityApiAdapter(CreditApiAdapter):

    def __init__(self, curve, eps=None, invisible=None):
        curve = DefaultProb(curve, invisible=True)
        curve = DiscountFactorApiAdapter(curve, eps=eps, invisible=True)
        super().__init__(curve, invisible=invisible)
