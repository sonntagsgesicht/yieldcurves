
from ..curve import DomainCurve
from ..interpolation import constant, linear, loglinearrate
from .wrapper import Df, Zero, Cash, Short, ZeroC, ZeroS, CashC, ZeroZ


class RateCurve(DomainCurve):

    forward_tenor = None

    def __init__(self, domain=(), data=(), interpolation=linear,
                 origin=None, day_count=None,
                 frequency=None, forward_tenor=None, **__):
        super().__init__(domain=domain, origin=origin, day_count=day_count)
        s = DomainCurve.interpolated(domain, data, interpolation, **__)
        self.curve = s.curve
        self.frequency = frequency
        self.forward_tenor = forward_tenor

        # to be set by subclass
        self.zero = self.short = self.df = self.cash = None

    def get_discount_factor(self, start, stop=None):
        start, stop = self._f(start), self._f(stop)
        if isinstance(self.df, Df):
            return self.df(start, stop)
        return self.df(stop) / self.df(start)

    def get_zero_rate(self, start, stop=None):
        start, stop = self._f(start), self._f(stop)
        if isinstance(self.zero, Zero):
            return self.zero(start, stop)
        raise NotImplementedError()

    def get_cash_rate(self, start, stop=None, step=None):
        if stop is None:
            if step is None:
                step = getattr(self, 'forward_tenor', None) \
                       or self.__class__.forward_tenor
            stop = start + step
        start, stop = self._f(start), self._f(stop)
        if isinstance(self.cash, Cash):
            return self.cash(stop, start)
        raise NotImplementedError()

    def get_short_rate(self, start):
        start = self._f(start)
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
                 origin=None, day_count=None,
                 frequency=None, forward_tenor=None, **__):
        super().__init__(domain=domain, data=data, interpolation=interpolation,
                         origin=origin, day_count=day_count,
                         frequency=frequency, forward_tenor=forward_tenor,
                         **__)
        self.zero = ZeroZ(self.curve)
        self.short = Short(self.zero)
        self.df = Df(self.zero, frequency)
        self.cash = Cash(self.zero, frequency, forward_tenor)


class ShortRateCurve(RateCurve):

    def __init__(self, domain=(), data=(), interpolation=constant,
                 origin=None, day_count=None,
                 frequency=None, forward_tenor=None, **__):
        super().__init__(domain=domain, data=data, interpolation=interpolation,
                         origin=origin, day_count=day_count,
                         frequency=frequency, forward_tenor=forward_tenor,
                         **__)
        self.short = self.curve
        self.zero = ZeroS(self.short)
        self.df = Df(self.zero, frequency)
        self.cash = Cash(self.zero, frequency, forward_tenor)


class CashRateCurve(RateCurve):

    def __init__(self, domain=(), data=(), interpolation=linear,
                 origin=None, day_count=None,
                 frequency=None, forward_tenor=None, **__):
        super().__init__(domain=domain, data=data, interpolation=interpolation,
                         origin=origin, day_count=day_count,
                         frequency=frequency, forward_tenor=forward_tenor,
                         **__)
        self.cash = CashC(self.curve)
        self.zero = ZeroC(self.cash)
        self.short = Short(self.zero)
        self.df = Df(self.zero)


class DiscountFactorCurve(RateCurve):

    def __init__(self, domain=(), data=(), interpolation=loglinearrate,
                 origin=None, day_count=None,
                 frequency=None, forward_tenor=None, **__):
        super().__init__(domain=domain, data=data, interpolation=interpolation,
                         origin=origin, day_count=day_count,
                         frequency=frequency, forward_tenor=forward_tenor,
                         **__)
        self.df = self.curve
        self.zero = Zero(self.df)
        self.short = Short(self.zero)
        self.cash = Cash(self.zero)
