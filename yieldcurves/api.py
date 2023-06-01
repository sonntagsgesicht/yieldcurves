
from .curve import DomainCurve
from .analytics import yield_curve, credit_curve, rate_curve, fx_curve, \
    nelson_siegel_svensson_curve, vol_curve
from .interpolation import constant, linear, loglinearrate


# --- api curves ---


class YieldCurve(DomainCurve):

    def __init__(self, domain=(), data=(), interpolation=linear,
                 origin=None, day_count=None,
                 spot_price=1.0, curve_type='yield'):
        super().__init__(domain, data, interpolation,
                         origin=origin, day_count=day_count)
        self.curve = yield_curve(self.curve,
                                 spot=spot_price, curve_type=curve_type)

    def get_forward_price(self, value_date):
        """ asset forward price at **value_date**

        derived by interpolation on given forward prices
        and extrapolation by given discount_factor resp. yield curve

        :param value_date: future date of asset price
        :return: asset forward price at **value_date**
        """
        return self.curve.price(self._f(value_date))

    def get_price_yield(self, value_date):
        return self.curve.price_yield(self._f(value_date))


class FxCurve(YieldCurve):
    """forward fx rate from spot rate as well
    domestic and foreign interest rate curve"""

    def __init__(self, spot_price=1.0, domestic_curve=0.0, foreign_curve=0.0,
                 origin=None, day_count=None):
        super().__init__(origin=origin, day_count=day_count)
        self.curve = fx_curve(spot_price, domestic=domestic_curve,
                              foreign=foreign_curve, curve_type='price')


class CreditCurve(DomainCurve):

    def __init__(self, domain=(), data=(), interpolation=loglinearrate,
                 origin=None, day_count=None, curve_type='prob'):
        super().__init__(domain, data, interpolation,
                         origin=origin, day_count=day_count)
        self.curve = credit_curve(self.curve, curve_type=curve_type)

    def get_survival_prob(self, start, stop=None):
        r"""survival probability of credit curve

        :param start: start point in time $t_0$ of period
        :param stop: end point $t_1$ of period
            (optional, if not given $t_0$ will be **origin**
            and $t_1$ taken from **start**)
        :return: survival probability $sv(t_0, t_1)$
            for period $t_0$ to $t_1$

        Assume an uncertain event $\chi$,
        e.g. occurrence of a credit default event
        such as a loan borrower failing to fulfill the obligation
        to pay back interest or redemption.

        Let $\iota_\chi$ be the point in time when the event $\chi$ happens.

        Then the survival probability $sv(t_0, t_1)$
        is the probability of not occurring $\chi$ until $t_1$ if
        $\chi$ didn't happen until $t_0$, i.e.

        $$sv(t_0, t_1) = 1 - P(t_0 < \iota_\chi \leq t_1)$$

        * similar to |InterestRateCurve().get_discount_factor()|

        """
        start = self._f(start)
        if stop is None:
            return self.curve.prob(start)
        stop = self._f(stop)
        return self.curve.prob(start) / self.curve.prob(stop)

    def get_flat_intensity(self, start, stop=None):
        r"""intensity value of credit curve

        :param start: start point in time $t_0$ of intensity
        :param stop: end point $t_1$  of intensity
            (optional, if not given $t_0$ will be **origin**
            and $t_1$ taken from **start**)
        :return: intensity $\lambda(t_0, t_1)$

        The intensity $\lambda(t_0, t_1)$ relates to survival probabilities by

        $$sv(t_0, t_1) = exp(-\lambda(t_0, t_1) \cdot \tau(t_0, t_1)).$$

        * similar to |InterestRateCurve().get_zero_rate()|

        """
        start = self._f(start)
        if stop is None:
            return self.curve.intensity(start)
        stop = self._f(stop)
        return self.curve.intensity(start, stop)

    def get_hazard_rate(self, start):
        r"""hazard rate of credit curve

        :param start: point in time $t$ of hazard rate
        :return: hazard rate $hz(t)$

        The hazard rate $hz(t)$ relates to intensities by

        $$\lambda(t_0, t_1) = \int_{t_0}^{t_1} hz(t)\ dt.$$

        * similar to |InterestRateCurve().get_short_rate()|

        """
        start = self._f(start)
        return self.curve.hazard_rate(start)


class RateCurve(DomainCurve):

    forward_tenor = None

    def __init__(self, domain=(), data=(), interpolation=linear,
                 origin=None, day_count=None,
                 frequency=None, forward_tenor=None, curve_type='zero'):
        super().__init__(domain, data, interpolation,
                         origin=origin, day_count=day_count)
        self.forward_tenor = forward_tenor
        self.curve = rate_curve(self.curve,
                                frequency=frequency, curve_type=curve_type)

    def get_discount_factor(self, start, stop=None):
        start = self._f(start)
        if stop is None:
            return self.curve.df(start)
        stop = self._f(stop)
        return self.curve.df(stop, start)

    def get_zero_rate(self, start, stop=None):
        start = self._f(start)
        if stop is None:
            return self.curve.zero(start)
        stop = self._f(stop)
        return self.curve.zero(stop, start)

    def get_cash_rate(self, start, stop=None, step=None):
        if stop is None:
            if step is None:
                step = self.__class__.forward_tenor
                step = getattr(self, 'forward_tenor', None) or step
            stop = start + step
        start = self._f(start)
        stop = self._f(stop)
        return self.curve.cash(stop, start)

    def get_short_rate(self, start):
        start = self._f(start)
        return self.curve.short(start)

    def get_swap_annuity(self, date_list=(), start=None, stop=None, step=None):
        if not date_list:
            if step is None:
                step = self.__class__.forward_tenor
                step = getattr(self, 'forward_tenor', None) or step
            date_list = [start]
            while date_list[-1] + step < stop:
                date_list.append(date_list[-1] + step)
            date_list.append(stop)
        return sum(self.get_discount_factor(s, e) * (e - s)
                   for s, e in zip(date_list[:-1], date_list[0:]))


class VolCurve(DomainCurve):

    def __init__(self, domain=(), data=(), interpolation=constant,
                 origin=None, day_count=None, curve_type='terminal'):
        super().__init__(domain, data, interpolation,
                         origin=origin, day_count=day_count)
        self.curve = vol_curve(self.curve, curve_type=curve_type)

    def get_instantaneous_vol(self, start):
        start = self._f(start)
        return self.curve.vol(start)

    def get_terminal_vol(self, start, stop=None):
        start = self._f(start)
        if stop is None:
            return self.curve.vol(start)
        stop = self._f(stop)
        return self.curve.vol(stop, start)


# --- parametric curve classes ---


class NeslonSiegelSvenssonZeroRateCurve(RateCurve):

    def __init__(self, beta0=0.0, beta1=0.0, beta2=0.0, beta3=0.0,
                 tau0=1.0, tau1=1.0, origin=None, day_count=None):
        super().__init__(origin=origin, day_count=day_count)
        curve = nelson_siegel_svensson_curve(
            beta0, beta1, beta2, beta3, tau0, tau1)
        self.curve = rate_curve(curve, curve_type='zero')

    def update(self):
        url = 'https://sdw-wsrest.ecb.europa.eu/' \
              'service/data/YC/B.U2.EUR.4F.G_N_A+G_N_C.SV_C_YM.?' \
              'lastNObservations=1&format=csvdata'
        file = 'data.cvs'
