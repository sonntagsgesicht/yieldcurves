
from .curve import DateCurve, InterpolatedDateCurve, ParametricDateCurve


from . import interpolation as _interpolation  # noqa E402
from .analytics import nss as _nss  # noqa E402
from .analytics import sabr as _sabr  # noqa E402
from .analytics import api as _api  # noqa E402
from .analytics.api import price_curve, yield_curve, fx_curve, prob_curve, \
    rate_curve, vol_curve


# --- api curves ---


class PriceCurve(DateCurve):

    def __init__(self, curve, spot=1.0, **kwargs):
        curve = price_curve(curve, spot)
        super().__init__(curve, **kwargs)

    def get_forward_price(self, value_date):
        """ asset forward price at **value_date**

        derived by interpolation on given forward prices
        and extrapolation by given discount_factor resp. yield curve

        :param value_date: future date of asset price
        :return: asset forward price at **value_date**
        """
        return self.curve.price(self._yf(value_date))

    def get_price_yield(self, value_date):
        return self.curve.price_yield(self._yf(value_date))


class YieldCurve(DateCurve):

    def __init__(self, curve, spot=1.0, **kwargs):
        curve = yield_curve(curve, spot)
        super().__init__(curve, **kwargs)

    def get_forward_price(self, value_date):
        """ asset forward price at **value_date**

        derived by interpolation on given forward prices
        and extrapolation by given discount_factor resp. yield curve

        :param value_date: future date of asset price
        :return: asset forward price at **value_date**
        """
        return self.curve.price(self._yf(value_date))

    def get_price_yield(self, value_date):
        return self.curve.price_yield(self._yf(value_date))


class FxCurve(PriceCurve):

    def __init__(self, spot=1.0, domestic=0.0, foreign=0.0, **kwargs):
        curve = fx_curve(spot, domestic, foreign)
        super().__init__(curve, **kwargs)


class CreditCurve(DateCurve):

    def __init__(self, curve, **kwargs):
        curve = prob_curve(curve)
        super().__init__(curve, **kwargs)

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
        start = self._yf(start)
        if stop is None:
            return self.curve.prob(start)
        stop = self._yf(stop)
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
        start = self._yf(start)
        if stop is None:
            return self.curve.intensity(start)
        stop = self._yf(stop)
        return self.curve.intensity(start, stop)

    def get_hazard_rate(self, start):
        r"""hazard rate of credit curve

        :param start: point in time $t$ of hazard rate
        :return: hazard rate $hz(t)$

        The hazard rate $hz(t)$ relates to intensities by

        $$\lambda(t_0, t_1) = \int_{t_0}^{t_1} hz(t)\ dt.$$

        * similar to |InterestRateCurve().get_short_rate()|

        """
        start = self._yf(start)
        return self.curve.hazard_rate(start)


class RateCurve(DateCurve):

    FORWARD_TENOR = None

    def __init__(self, curve, frequency=None, forward_tenor=None, **kwargs):
        curve = rate_curve(curve, frequency=frequency)
        forward_tenor = forward_tenor or self.FORWARD_TENOR
        super().__init__(curve, forward_tenor=forward_tenor, **kwargs)

    def get_discount_factor(self, start, stop=None):
        start = self._yf(start)
        if stop is None:
            return self.df(start)
        stop = self._yf(stop)
        return self.curve.df(stop, start)

    def get_zero_rate(self, start, stop=None):
        start = self._yf(start)
        if stop is None:
            return self.curve.zero(start)
        stop = self._yf(stop)
        return self.curve.zero(stop, start)

    def get_cash_rate(self, start, stop=None, step=None):
        start = self._yf(start)
        if stop is None:
            if step is None:
                step = self.forward_tenor
            stop = start + step
        stop = self._yf(stop)
        return self.curve.cash(self.df, stop, start)

    def get_short_rate(self, start):
        start = self._yf(start)
        return self.curve.short(start)

    def get_swap_annuity(self, date_list=(), start=None, stop=None, step=None):
        if not date_list:
            step = self.compounding_frequency if step is None else step
            date_list = [start]
            while date_list[-1] + step < stop:
                date_list.append(date_list[-1] + step)
            date_list.append(stop)
        return sum(self.get_discount_factor(s, e) * (e - s)
                   for s, e in zip(date_list[:-1], date_list[0:]))


class VolatilityCurve(DateCurve):

    def __init__(self, curve, **kwargs):
        curve = vol_curve(curve)
        super().__init__(curve, **kwargs)

    def get_instantaneous_vol(self, start):
        start = self._yf(start)
        return self.curve.vol(start)

    def get_terminal_vol(self, start, stop=None):
        start = self._yf(start)
        if stop is None:
            return self.curve.vol(start)
        stop = self._yf(stop)
        return self.curve.vol(stop, start)


# --- price yield curves ---


class ForwardPriceCurve(PriceCurve, InterpolatedDateCurve):
    """forward price from spot price and yield curve"""

    curve_type = _api.price
    interpolation_type = _interpolation.loglinearrate


class PriceYieldCurve(PriceCurve, InterpolatedDateCurve):
    """forward price from spot price and yield curve"""

    curve_type = _api.price_yield
    interpolation_type = _interpolation.linear


class ForwardFxCurve(PriceCurve, InterpolatedDateCurve):
    """forward fx rate from spot rate as well
    domestic and foreign interest rate curve"""

    curve_type = _api.fx
    interpolation_type = _interpolation.linear


# --- credit probability curve classes ---


class SurvivalProbabilityCurve(CreditCurve,
                               InterpolatedDateCurve):

    curve_type = _api.prob
    interpolation_type = _interpolation.loglinearrate


class DefaultProbabilityCurve(CreditCurve,
                              InterpolatedDateCurve):

    curve_type = _api.pd
    interpolation_type = _interpolation.loglinearrate


class MarginalSurvivalProbabilityCurve(CreditCurve,
                                       InterpolatedDateCurve):

    curve_type = _api.marginal
    interpolation_type = _interpolation.loglinear


class IntensityProbabilityCurve(CreditCurve, InterpolatedDateCurve):

    curve_type = _api.intensity
    interpolation_type = _interpolation.linear


class HazardRateProbabilityCurve(CreditCurve, InterpolatedDateCurve):

    curve_type = _api.hazard_rate
    interpolation_type = _interpolation.constant


# --- interest rate curve classes ---


class ZeroRateCurve(RateCurve, InterpolatedDateCurve):

    curve_type = _api.zero
    interpolation_type = _interpolation.linear


class CashRateCurve(RateCurve, InterpolatedDateCurve):

    curve_type = _api.cash
    interpolation_type = _interpolation.linear


class ShortRateCurve(RateCurve, InterpolatedDateCurve):

    curve_type = _api.short
    interpolation_type = _interpolation.constant


# --- volatility curve classes ---


class InstantaneousVolatilityCurve(VolatilityCurve, InterpolatedDateCurve):

    curve_type = _api.instantaneous
    interpolation_type = _interpolation.constant


class TerminalVolatilityCurve(VolatilityCurve, InterpolatedDateCurve):

    curve_type = _api.terminal
    interpolation_type = _interpolation.constant


# --- parametric curve classes ---


class NeslonSiegelSvenssonZeroRateCurve(RateCurve, ParametricDateCurve):

    curve_type = _api.zero
    functional_type = _nss.nelson_siegel_svensson


class SabrVol(VolatilityCurve, ParametricDateCurve):

    curve_type = _api.terminal
    functional_type = _sabr.sabr
