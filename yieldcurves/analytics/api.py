from ..tools.adapter import CurveAdapter, init_curve
from .rate import CompoundingRate, CompoundingFactor
from .price import PriceAdapter, PriceYieldAdapter
from .interest import CashRateAdapter, ShortRateAdapter, \
    CompoundingShortRateAdapter, CompoundingCashRateAdapter


class PriceApiAdapter(CurveAdapter):

    def __init__(self, curve, spot=1.0, fx=1.0, foreign=0.0,
                 *, invisible=None):
        super().__init__(init_curve(curve), invisible=invisible)
        self._price = PriceAdapter(self.curve, spot, fx, foreign,
                                   invisible=True)
        self._yield = PriceYieldAdapter(self.curve, spot, fx, foreign,
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
        self.cash = CashRateAdapter(self.zero, frequency, invisible=True)
        self.short = ShortRateAdapter(self.zero, frequency, eps,
                                       invisible=True)


class DiscountFactorApiAdapter(ZeroRateApiAdapter):

    def __init__(self, curve, frequency=None, eps=None, invisible=None):
        curve = CompoundingRate(curve, frequency, invisible=True)
        super().__init__(curve, frequency, eps, invisible=invisible)


class ShortRateApiAdapter(ZeroRateApiAdapter):

    def __init__(self, curve, frequency=None, eps=None, invisible=None):
        curve = CompoundingShortRateAdapter(curve, frequency, invisible=True)
        super().__init__(curve, frequency, eps, invisible=invisible)
        self.short = self.curve


class CashRateApiAdapter(ZeroRateApiAdapter):

    def __init__(self, curve, frequency=None, eps=None, invisible=None):
        cash = curve
        curve = CompoundingCashRateAdapter(curve, frequency, invisible=True)
        super().__init__(curve, frequency, eps, invisible=invisible)
        self.cash = lambda x, y=None: cash(x)


class _Api(CurveAdapter):

    adapter = None

    def __init__(self, curve, **__):
        curve = self.adapter(curve, invisible=None)
        super().__init__(curve, **__)

    def prob(self, x, y=None):
        return self.curve.df(x, y)

    def pd(self, x, y=None):
        return 1. - self.prob(x, y)

    def marginal(self, x):
        return self.prob(x, x + 1.)

    def intensity(self, x, y=None):
        return self.curve.zero(x, y)

    def hazard_rate(self, x):
        return self.curve.short(x)


FlatIntensityApiAdapter = \
    type('FlatIntensityApiAdapter', (_Api, ), {'adapter': ZeroRateApiAdapter})

HazardRateApiAdapter = \
    type('HazardRateApiAdapter', (_Api, ShortRateApiAdapter), {})


SurvivalProbabilityApiAdapter = \
    type('SurvivalProbabilityApiAdapter', (_Api, DiscountFactorApiAdapter), {})


class MarginalSurvivalProbabilityApiAdapter(_Api, DiscountFactorApiAdapter):

    def __init__(self, curve):

        super().__init__(curve)


class DefaultProbabilityApiAdapter(CurveAdapter):
    pass
