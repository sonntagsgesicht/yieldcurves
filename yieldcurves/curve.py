
from .tools.curve import CurveAdapter, init_curve

from . import interpolation as _interpolation
from .daycount import YearFraction
from .interpolation import linear
from .api import RateApi, FxApi, PriceApi, CreditApi
from .analytics.interest import ZeroRateAdapter, DiscountFactorAdapter, \
    ShortRateAdapter, CashRateAdapter
from .analytics.fx import FxRateAdapter
from .analytics.price import YieldCurveAdapter
from .analytics.credit import DefaultProbabilityAdapter, \
    SurvivalProbabilityAdapter, MarginalSurvivalProbabilityAdapter, \
    HazardRateAdapter, FlatIntensityAdapter


class InterpolatedDateCurve(CurveAdapter):

    def __init__(self, domain=(), data=(), interpolation=linear,
                 origin=None, day_count=None, **__):
        r"""
        :param domain: either curve points $t_1 \dots t_n$
            or a curve object $C$
        :param data: either curve values $y_1 \dots y_n$
            or a curve object $C$
        :param interpolation: (optional) interpolation scheme
        :param origin: (optional) curve points origin $t_0$
        :param day_count: (optional) day count convention function $\tau(s, t)$
        :param forward_tenor: (optional) forward rate tenor period $\tau^*$

        If **data** is a |RateCurve| instance $C$,
        it is casted to this new class type
        with domain grid given by **domain**.

        If **domain** is a |RateCurve| instance $C$,
        it is casted to this new class type
        with domain grid given **domain** property of $C$.

        Further arguments
        **interpolation**, **origin**, **day_count**, **forward_tenor**
        will replace the ones given by $C$ if not given explictly.

        """
        domain = tuple(domain)

        # build yf transformer, transform domain and build inner curve
        yf = YearFraction(day_count, origin=origin, domain=domain)
        i_type = getattr(_interpolation, str(interpolation), interpolation)
        curve = i_type(yf(domain), data, **__)
        super().__init__(curve, pre=yf, inv=yf.inv)

        # save properties
        self.domain = domain
        self.origin = origin
        self.day_count = day_count
        self.interpolation = getattr(i_type, '__name__', str(interpolation))


class _RateCurve(InterpolatedDateCurve, RateApi):

    adapter = None

    def __init__(self, domain=(), data=(), interpolation=linear,
                 origin=None, day_count=None, forward_tenor=None, **__):
        r"""
        :param domain: either curve points $t_1 \dots t_n$
            or a curve object $C$
        :param data: either curve values $y_1 \dots y_n$
            or a curve object $C$
        :param interpolation: (optional) interpolation scheme
        :param origin: (optional) curve points origin $t_0$
        :param day_count: (optional) day count convention function $\tau(s, t)$
        :param forward_tenor: (optional) forward rate tenor period $\tau^*$

        If **data** is a |RateCurve| instance $C$,
        it is casted to this new class type
        with domain grid given by **domain**.

        If **domain** is a |RateCurve| instance $C$,
        it is casted to this new class type
        with domain grid given **domain** property of $C$.

        Further arguments
        **interpolation**, **origin**, **day_count**, **forward_tenor**
        will replace the ones given by $C$ if not given explictly.

        """
        super().__init__(domain, data, interpolation=interpolation,
                         origin=origin, day_count=day_count, **__)
        frequency = 1 / self._pre(origin + forward_tenor)
        self.curve = self.adapter(self.curve, frequency, invisible=True)
        self.forward_tenor = forward_tenor


ZeroRateCurve = \
    type('ZeroRateCurve', (_RateCurve,), {'adapter': ZeroRateAdapter})
ShortRateCurve = \
    type('ShortRateCurve', (_RateCurve,), {'adapter': ShortRateAdapter})
CashRateCurve = \
    type('CashRateCurve', (_RateCurve,), {'adapter': CashRateAdapter})
DiscountFactorCurve = \
    type('DiscountFactorCurve', (_RateCurve,), {'adapter': DiscountFactorAdapter})


class FxRateCurve(InterpolatedDateCurve, FxApi):

    def __init__(self, domain=(), data=(), interpolation=linear,
                 origin=None, day_count=None, domestic=0.0, foreign=0.0, **__):
        r"""
        :param domain: either curve points $t_1 \dots t_n$
            or a curve object $C$
        :param data: either curve values $y_1 \dots y_n$
            or a curve object $C$
        :param interpolation: (optional) interpolation scheme
        :param origin: (optional) curve points origin $t_0$
        :param day_count: (optional) day count convention function $\tau(s, t)$
        :param domestic: (optional) forward rate tenor period $\tau^*$
        :param foreign: (optional) forward rate tenor period $\tau^*$

        If **data** is a |RateCurve| instance $C$,
        it is cast to this new class type
        with domain grid given by **domain**.

        If **domain** is a |RateCurve| instance $C$,
        it is cast to this new class type
        with domain grid given **domain** property of $C$.

        Further arguments
        **interpolation**, **origin**, **day_count**, **domestic**, **foreign**
        will replace the ones given by $C$ if not given explicitly.

        """
        super().__init__(domain, data, interpolation=interpolation,
                         origin=origin, day_count=day_count, **__)
        self.curve = FxRateAdapter(self.curve, init_curve(domestic).curve,
                                   init_curve(foreign).curve, invisible=True)
        self.domestic = domestic
        self.foreign = foreign


class PriceCurve(InterpolatedDateCurve, PriceApi):

    def __init__(self, domain=(), data=(), interpolation=linear,
                 origin=None, day_count=None, yield_rate=0.0, **__):
        """

        :param domain:
        :param data:
        :param interpolation:
        :param origin:
        :param day_count:
        :param yield_rate:
        :param __:
        """
        super().__init__(domain, data, interpolation=interpolation,
                         origin=origin, day_count=day_count, **__)
        self.curve = YieldCurveAdapter(init_curve(yield_rate).curve,
                                       spot=self.curve, invisible=True)
        self.yield_rate = yield_rate


class YieldCurve(InterpolatedDateCurve, PriceApi):

    def __init__(self, domain=(), data=(), interpolation=linear,
                 origin=None, day_count=None, spot=0.0, **__):
        """

        :param domain:
        :param data:
        :param interpolation:
        :param origin:
        :param day_count:
        :param yield_rate:
        :param __:
        """
        super().__init__(domain, data, interpolation=interpolation,
                         origin=origin, day_count=day_count, **__)
        self.curve = YieldCurveAdapter(self.curve,
                                       spot=init_curve(spot).curve,
                                       invisible=True)
        self.spot = spot


class _CreditCurve(InterpolatedDateCurve, CreditApi):

    adapter = None

    def __init__(self, domain=(), data=(), interpolation=linear,
                 origin=None, day_count=None, **__):
        r"""
        :param domain: either curve points $t_1 \dots t_n$
            or a curve object $C$
        :param data: either curve values $y_1 \dots y_n$
            or a curve object $C$
        :param interpolation: (optional) interpolation scheme
        :param origin: (optional) curve points origin $t_0$
        :param day_count: (optional) day count convention function $\tau(s, t)$
        :param forward_tenor: (optional) forward rate tenor period $\tau^*$

        If **data** is a |RateCurve| instance $C$,
        it is casted to this new class type
        with domain grid given by **domain**.

        If **domain** is a |RateCurve| instance $C$,
        it is casted to this new class type
        with domain grid given **domain** property of $C$.

        Further arguments
        **interpolation**, **origin**, **day_count**, **forward_tenor**
        will replace the ones given by $C$ if not given explictly.

        """
        super().__init__(domain, data, interpolation=interpolation,
                         origin=origin, day_count=day_count, **__)
        self.curve = self.adapter(self.curve, invisible=True)


HazardRateCurve = \
    type('HazardRateCurve', (_CreditCurve,),
         {'adapter': HazardRateAdapter})
FlatIntensityCurve = \
    type('FlatIntensityCurve', (_CreditCurve,),
         {'adapter': FlatIntensityAdapter})
SurvivalProbabilityCurve = \
    type('SurvivalProbabilityCurve', (_CreditCurve,),
         {'adapter': SurvivalProbabilityAdapter})
MarginalSurvivalProbabilityCurve = \
    type('MarginalSurvivalProbabilityCurve', (_CreditCurve,),
         {'adapter': MarginalSurvivalProbabilityAdapter})
DefaultProbabilityCurve = \
    type('DefaultProbabilityCurve', (_CreditCurve,),
         {'adapter': DefaultProbabilityAdapter})