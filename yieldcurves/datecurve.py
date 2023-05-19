from datetime import date

from . import yieldcurve as _yieldcurve
from . import interpolation as _interpolation
from . import parametric as _parametric
from .curve import init_curve
from .daycount import day_count as _day_count
from .repr import representation


def item_name(cls, item, default=None):
    if item is None:
        if default is None:
            return (lambda x: x), None
        return default, None
    if isinstance(item, str):
        return getattr(cls, item), item,
    return getattr(item, '__name__', str(item)), item


def origin_default(x):
    return date.today() if isinstance(x, date) else type(x)()


class DateCurve:
    """ This is a DateCurve

        >>> from yieldcurves.datecurve import DateCurve

        >>> domain = 0, 5
        >>> data = 0.02, 0.04
        >>> curve = DateCurve(domain, data)
        >>> curve

        >>> curve(2)

        >>> from datetime import date

        >>> domain = date(2020, 2, 1), date(2025, 2, 1)
        >>> data = 0.02, 0.04
        >>> curve = DateCurve(domain, data)
        >>> curve

        >>> curve(date(2022, 2, 1))

        >>> from businessdate import BusinessDate as bd
        >>> from businessdate import BusinessSchedule as bs

        >>> today = bd(20200201)
        >>> domain = bs(today, '5y', '1y')
        >>> data = .02, .025, .03, .03, .04
        >>> curve = DateCurve(domain, data)
        >>> curve

        >>> curve(bd(20220201))

    """
    __slots__ = '_curve', '_day_count', '_origin', '_as', '_kws'
    ORIGIN = 0.0

    @property
    def curve(self):
        return self._curve

    @property
    def origin(self):
        return self._origin

    @property
    def day_count(self):
        if self._day_count is None:
            return _day_count
        return self._day_count

    def __init__(self, curve=None, day_count=None, origin=None):
        """
        :param curve: underlying curve
        :param day_count: function to calculate year fractions
            (time between dates as a float)
        :param origin: origin date of curve
        """

        # save initial arguments
        _args = curve,
        _kwargs = {'day_count': day_count, 'origin': origin}

        # build curve
        if isinstance(curve, DateCurve):
            day_count = day_count or curve.day_count
            origin = origin or curve.origin
            curve = curve.curve

        # set properties
        self._day_count = day_count
        self._origin = origin
        self._curve = curve

        # store arguments
        self._as, self._kws = _args, _kwargs

    def __str__(self):
        return representation(self, *self._as, **self._kws, rstyle=False)

    def __repr__(self):
        return representation(self, *self._as, **self._kws)

    def __getattr__(self, item):
        if hasattr(self._curve, item):
            attr = getattr(self._curve, item)
            if not callable(attr):
                return attr
            return lambda *a, **kw: attr(*self._yf(a), **self._yf(kw))
        return self.__getattribute__(item)

    def __getitem__(self, item):
        return self._curve[self._yf(item)]

    def __setitem__(self, key, value):
        self._curve[self._yf(key)] = value

    def __delitem__(self, key):
        del self._curve[self._yf(key)]

    def __iter__(self):
        # inverse of day_count(origin, x) -> origin + yf
        return iter(self.origin + yf for yf in self.curve)

    def __contains__(self, item):
        return self._yf(item) in self.curve

    def __call__(self, x, *args, **kwargs):
        return self._curve(self._yf(x), *self._yf(args), **self._yf(kwargs))

    def _yf(self, x):
        if not x:
            return x
        day_count = self.day_count
        origin = self._origin
        if isinstance(x, (list, tuple)):
            origin = origin_default(x[0]) if origin is None else origin
            return type(x)([day_count(origin, a) for a in x])
        if isinstance(x, dict):
            y, *_ = x.values()
            origin = origin_default(y) if origin is None else origin
            return dict((k, day_count(origin, v)) for k, v in x.items())

        origin = origin_default(x) if origin is None else origin
        return day_count(origin, x)


class DateYieldCurve(DateCurve):
    __slots__ = '_curve', '_day_count', '_origin', '_as', '_kws'

    yieldcurve_type = None

    def __init__(self, curve, yield_curve_type=None,
                 day_count=None, origin=None, **kwargs):

        # gather yield_curve_type
        yc_type, yc_name = item_name(curve, yield_curve_type,
                                     default=self.__class__.yieldcurve_type)

        # build curve
        super().__init__(yc_type(curve, **kwargs), day_count, origin)

        # store arguments
        self._as = curve, yc_name
        self._kws.update(kwargs)


class InterpolatedDateYieldCurve(DateYieldCurve):
    __slots__ = '_curve', '_domain', '_day_count', '_origin', '_as', '_kws'

    interpolation_type = None

    def __init__(self, domain, data=None, interpolation=None,
                 yield_curve_type=None,
                 day_count=None, origin=None, **kwargs):

        # gather interpolation
        i_type, i_name = item_name(_interpolation, interpolation,
                                   default=self.__class__.interpolation_type)

        # build curve
        self._domain = domain
        if data is None:
            # if no data given bypass i_type build
            i_curve = init_curve(domain)
        else:
            _dc = day_count or _day_count
            _origin = origin or origin_default(domain[0])
            _domain = type(domain)(tuple(_dc(_origin, d) for d in domain))
            i_curve = i_type(_domain, data)
        super().__init__(i_curve, yield_curve_type,
                         day_count=day_count, origin=origin, **kwargs)

        # store arguments
        self._as = domain,
        if data is not None:
            self._as += data,
        self._kws['interpolation'] = i_name

    def __iter__(self):
        if isinstance(self._domain, (int, float)):
            return iter([])
        return iter(self._domain)


class ParametricDateYieldCurve(DateYieldCurve):
    __slots__ = '_curve', '_day_count', '_origin', '_as', '_kws'

    functional_type = None

    def __init__(self, param, func=None, yield_curve_type=None,
                 day_count=None, origin=None, **kwargs):
        # gather interpolation
        f_type, f_name = item_name(_parametric, func,
                                   default=self.__class__.functional_type)

        # build curve
        if func is None:
            # if no data given bypass f_type build
            f_curve = param
        elif isinstance(param, (list, tuple)):
            f_curve = f_type(*param)
        elif isinstance(param, dict):
            f_curve = f_type(**param)
        else:
            f_curve = f_type(param)

        super().__init__(f_curve, yield_curve_type,
                         day_count=day_count, origin=origin, **kwargs)

        # store arguments
        self._as = f_name, param,


# --- price curve classes ---


class PriceCurve(InterpolatedDateYieldCurve):
    """forward price from spot price and yield curve"""

    yieldcurve_type = _yieldcurve.price_curve
    interpolation_type = _interpolation.loglinearrate


class YieldCurve(InterpolatedDateYieldCurve):
    """price yield from price curve"""

    yieldcurve_type = _yieldcurve.yield_curve
    interpolation_type = _interpolation.linear


class FxCurve(InterpolatedDateYieldCurve):
    """forward fx rate from spot rate as well
    domestic and foreign interest rate curve"""

    yieldcurve_type = _yieldcurve.fx_curve
    interpolation_type = _interpolation.linear


# --- credit probability curve classes ---


class SurvivalProbabilityCurve(InterpolatedDateYieldCurve):

    yieldcurve_type = _yieldcurve.survival_probability_curve
    interpolation_type = _interpolation.loglinearrate


class DefaultProbabilityCurve(InterpolatedDateYieldCurve):

    yieldcurve_type = _yieldcurve.default_probability_curve
    interpolation_type = _interpolation.loglinearrate


class MarginalSurvivalProbabilityCurve(InterpolatedDateYieldCurve):

    yieldcurve_type = _yieldcurve.marginal_survival_probability_curve
    interpolation_type = _interpolation.loglinear


class IntensityProbabilityCurve(InterpolatedDateYieldCurve):

    yieldcurve_type = _yieldcurve.intensity_probability_curve
    interpolation_type = _interpolation.linear


class HazardRateProbabilityCurve(InterpolatedDateYieldCurve):

    yieldcurve_type = _yieldcurve.hazard_rate_probability_curve
    interpolation_type = _interpolation.constant


# --- interest rate curve classes ---


class ZeroRateCurve(InterpolatedDateYieldCurve):

    yieldcurve_type = _yieldcurve.zero_rate_curve
    interpolation_type = _interpolation.linear


class CashRateCurve(InterpolatedDateYieldCurve):

    yieldcurve_type = _yieldcurve.cash_rate_curve
    interpolation_type = _interpolation.linear


class ShortRateCurve(InterpolatedDateYieldCurve):

    yieldcurve_type = _yieldcurve.short_Rate_curve
    interpolation_type = _interpolation.constant


# --- parametric curve classes ---


class NeslonSiegelSvenssonZeroRateCurve(ParametricDateYieldCurve):

    yieldcurve_type = _yieldcurve.zero_rate_curve
    functional_type = _parametric.NelsonSiegelSvensson


class NeslonSiegelSvenssonCashRateCurve(ParametricDateYieldCurve):

    yieldcurve_type = _yieldcurve.cash_rate_curve
    functional_type = _parametric.NelsonSiegelSvensson


class SabrVol(ParametricDateYieldCurve):

    yieldcurve_type = _yieldcurve.terminal_volatility_curve
    functional_type = _parametric.SABR

