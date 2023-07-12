from ..curve import CurveAdapter
from .interest import ZeroRateAdapter, DiscountFactorAdapter, ShortRateAdapter


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


FlatIntensityAdapter = \
    type('FlatIntensityAdapter', (_Api, ), {'adapter': ZeroRateAdapter})

HazardRateAdapter = \
    type('HazardRateAdapter', (_Api, ShortRateAdapter), {})


SurvivalProbabilityAdapter = \
    type('SurvivalProbabilityAdapter', (_Api, DiscountFactorAdapter), {})


class MarginalSurvivalProbabilityAdapter(_Api, DiscountFactorAdapter):

    def __init__(self, curve):

        super().__init__(curve)


class DefaultProbabilityAdapter(CurveAdapter):
    pass
