
from ..curve import DomainCurve
from ..interpolation import constant, linear, loglinearrate
from .wrapper import Marginal, Prob, Pd, IntensityHz, Intensity, HazardRate, \
    ProbPd, IntensityI


class CreditCurve(DomainCurve):

    def __init__(self, domain=(), data=(), interpolation=loglinearrate,
                 origin=None, day_count=None, **__):
        super().__init__(domain=domain, origin=origin, day_count=day_count)
        s = DomainCurve.interpolated(domain, data, interpolation, **__)
        self.curve = s.curve

        self.prob = self.marginal = self.intensity = self.hazard_rate \
            = self.pd = None

    def get_default_prob(self, start, stop=None):
        r"""default probability of credit curve

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
        start, stop = self._f(start), self._f(stop)
        if isinstance(self.pd, Pd):
            return self.pd(start, stop)
        return 1. - (1. - self.pd(stop)) / (1. - self.pd(start))

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
        start, stop = self._f(start), self._f(stop)
        if isinstance(self.prob, Prob):
            return self.prob(start, stop)
        return self.prob(stop) / self.prob(start)

    def get_marginal_prob(self, start, stop=None):
        r"""marginal survival probability of credit curve

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
        start, stop = self._f(start), self._f(stop)
        if isinstance(self.marginal, Marginal):
            return self.marginal(start, stop)
        raise NotImplementedError()

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
        start, stop = self._f(start), self._f(stop)
        if isinstance(self.intensity, Intensity):
            return self.intensity(start, stop)
        raise NotImplementedError()

    def get_hazard_rate(self, start):
        r"""hazard rate of credit curve

        :param start: point in time $t$ of hazard rate
        :return: hazard rate $hz(t)$

        The hazard rate $hz(t)$ relates to intensities by

        $$\lambda(t_0, t_1) = \int_{t_0}^{t_1} hz(t)\ dt.$$

        * similar to |InterestRateCurve().get_short_rate()|

        """
        start = self._f(start)
        return self.hazard_rate(start)


class HazardRateCurve(CreditCurve):

    def __init__(self, domain=(), data=(), interpolation=constant,
                 origin=None, day_count=None, **__):
        super().__init__(domain=domain, data=data, interpolation=interpolation,
                         origin=origin, day_count=day_count, **__)

        self.hazard_rate = self.curve
        self.intensity = IntensityHz(self.hazard_rate)
        self.prob = Prob(self.intensity)
        self.marginal = Marginal(self.prob)
        self.pd = Pd(self.prob)


class FlatIntensityCurve(CreditCurve):

    def __init__(self, domain=(), data=(), interpolation=linear,
                 origin=None, day_count=None, **__):
        super().__init__(domain=domain, data=data, interpolation=interpolation,
                         origin=origin, day_count=day_count, **__)

        self.intensity = IntensityI(self.curve)
        self.hazard_rate = HazardRate(self.intensity)
        self.prob = Prob(self.intensity)
        self.marginal = Marginal(self.prob)
        self.pd = Pd(self.prob)


class SurvivalProbabilityCurve(CreditCurve):

    def __init__(self, domain=(), data=(), interpolation=loglinearrate,
                 origin=None, day_count=None, **__):
        super().__init__(domain=domain, data=data, interpolation=interpolation,
                         origin=origin, day_count=day_count, **__)

        self.prob = self.curve
        self.intensity = Intensity(self.prob)
        self.hazard_rate = HazardRate(self.intensity)
        self.marginal = Marginal(self.prob)
        self.pd = Pd(self.prob)


class MarginalSurvivalProbabilityCurve(CreditCurve):

    def __init__(self, domain=(), data=(), interpolation=loglinearrate,
                 origin=None, day_count=None, **__):
        super().__init__(domain=domain, data=data, interpolation=interpolation,
                         origin=origin, day_count=day_count, **__)

        self.marginal = self.curve
        self.prob = None
        self.intensity = Intensity(self.prob)
        self.hazard_rate = HazardRate(self.intensity)
        self.pd = Pd(self.prob)


class DefaultProbabilityCurve(CreditCurve):

    def __init__(self, domain=(), data=(), interpolation=loglinearrate,
                 origin=None, day_count=None, **__):
        super().__init__(domain=domain, data=data, interpolation=interpolation,
                         origin=origin, day_count=day_count, **__)

        self.pd = self.curve
        self.prob = ProbPd(self.pd)
        self.intensity = Intensity(self.prob)
        self.hazard_rate = HazardRate(self.intensity)
        self.marginal = Marginal(self.prob)
