
from .. import interpolation as _interpolation
from ..curve import CurveAdapter
from ..daycount import YearFraction
from ..interpolation import constant, linear, loglinearrate
from ..analytics.rate import Df, Zero, Cash, Short, ZeroC, ZeroS, CashC, ZeroZ


class RateCurve(CurveAdapter):

    forward_tenor = None

    def __init__(self, domain=(), data=(), interpolation=linear,
                 origin=None, day_count=None, forward_tenor=None, **__):
        domain = tuple(domain)

        # build yf transformer, transform domain and build inner curve
        yf = YearFraction(origin, day_count, domain=domain)
        i_type = getattr(_interpolation, str(interpolation), interpolation)
        super().__init__(i_type(yf(domain), data), pre=yf, **__)

        # save properties
        self.domain = domain
        self.origin = origin
        self.day_count = day_count
        self.interpolation = getattr(i_type, '__name__', str(interpolation))

        self.forward_tenor = forward_tenor

        # to be set by subclass
        self.zero = self.short = self.df = self.cash = None

    def get_discount_factor(self, start, stop=None):
        start, stop = self._pre(start), self._pre(stop)
        if isinstance(self.df, Df):
            return self.df(start, stop)
        return self.df(stop) / self.df(start)

    def get_zero_rate(self, start, stop=None):
        start, stop = self._pre(start), self._pre(stop)
        if isinstance(self.zero, Zero):
            return self.zero(start, stop)
        raise NotImplementedError()

    def get_cash_rate(self, start, stop=None, step=None):
        if stop is None:
            if step is None:
                step = getattr(self, 'forward_tenor', None) \
                       or self.__class__.forward_tenor
            stop = start + step
        start, stop = self._pre(start), self._pre(stop)
        if isinstance(self.cash, Cash):
            return self.cash(start, stop)
        raise NotImplementedError()

    def get_short_rate(self, start):
        start = self._pre(start)
        return self.short(start)

    def get_swap_annuity(self, date_list=(), start=None, stop=None, step=None):
        if not date_list:
            if step is None:
                step = getattr(self, 'forward_tenor', None) \
                       or self.__class__.forward_tenor
            date_list = [start]
            while date_list[-1] + step < stop:
                date_list.append(date_list[-1] + step)
            date_list.append(stop)

        se = zip(date_list[:-1], date_list[0:])
        return sum(self.get_discount_factor(s, e) * (e - s) for s, e in se)


class ZeroRateCurve(RateCurve):

    def __init__(self, domain=(), data=(), interpolation=linear,
                 origin=None, day_count=None, forward_tenor=None, **__):
        super().__init__(domain=domain, data=data, interpolation=interpolation,
                         origin=origin, day_count=day_count,
                         forward_tenor=forward_tenor, **__)
        frequency = 1 / self._pre(self.origin + self.forward_tenor)
        self.zero = ZeroZ(self.curve, frequency=frequency)
        self.short = Short(self.zero)
        self.df = Df(self.zero, frequency=frequency)
        self.cash = Cash(self.zero, frequency=frequency)


class ShortRateCurve(RateCurve):

    def __init__(self, domain=(), data=(), interpolation=constant,
                 origin=None, day_count=None, forward_tenor=None, **__):
        super().__init__(domain=domain, data=data, interpolation=interpolation,
                         origin=origin, day_count=day_count,
                         forward_tenor=forward_tenor, **__)
        frequency = 1 / self._pre(self.origin + self.forward_tenor)
        self.short = self.curve
        self.zero = ZeroS(self.short, frequency=frequency)
        self.df = Df(self.zero, frequency=frequency)
        self.cash = Cash(self.zero, frequency=frequency)


class CashRateCurve(RateCurve):

    def __init__(self, domain=(), data=(), interpolation=linear,
                 origin=None, day_count=None, forward_tenor=None, **__):
        super().__init__(domain=domain, data=data, interpolation=interpolation,
                         origin=origin, day_count=day_count,
                         forward_tenor=forward_tenor, **__)
        frequency = 1/self._pre(self.origin + self.forward_tenor)
        self.cash = CashC(self.curve, frequency=frequency)
        self.zero = ZeroC(self.cash, frequency=frequency)
        self.short = Short(self.zero)
        self.df = Df(self.zero, frequency=frequency)


class DiscountFactorCurve(RateCurve):

    def __init__(self, domain=(), data=(), interpolation=loglinearrate,
                 origin=None, day_count=None, forward_tenor=None, **__):
        super().__init__(domain=domain, data=data, interpolation=interpolation,
                         origin=origin, day_count=day_count,
                         forward_tenor=forward_tenor, **__)
        frequency = 1/self._pre(self.forward_tenor)
        self.df = self.curve
        self.zero = Zero(self.df, frequency=frequency)
        self.short = Short(self.zero)
        self.cash = Cash(self.zero, frequency=frequency)
