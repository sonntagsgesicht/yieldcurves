
from ..tools.fulladapter import CurveAdapter


class RateApi(CurveAdapter):

    def get_discount_factor(self, start, stop=None):
        r"""discounting factor for future cashflows

        :param start: date $t_0$ to discount to
        :param stop: date $t_1$ for discounting from
            (optional, if not given $t_0$ will be **origin**
            and $t_1$ by **start**)
        :return: discounting factor $df(t_0, t_1)$

        Assuming a constant bank account interest rate $r$
        over time and interest rate compounding a bank account of $B_0=1$
        at time $t_0$ will be some value $B_1$ at time $t_1$.

        For continuous compounding $B_1=B_0 * \exp(r\cdot (t_1-t_0))$,
        for more concepts of compounding see |yieldcurves.compounding|.

        Since $B_1$ is equivalent to the value of $B_0$ at time $t_1$,
        $B_0/B_1$ can be understood to as the price at time $t_0$
        of a bank account of $1$ at $t_1$.

        In general, discount factor $df(t_0, t_1)= B_0/B_1$ are used to
        give the price or present value $v_0(CF)$ at time $t_0$
        of any cashflow $CF$ at time $t_1$ by

        $$v_0(CF) = df(t_0, t_1) \cdot CF.$$

        This concept relates to the zero bond yields
        |InterestRateCurve().get_zero_rate()|.

        """
        start, stop = self._pre(start), self._pre(stop)
        return self.curve.df(start, stop)

    def get_zero_rate(self, start, stop=None):
        r"""curve of zero rates, i.e. yields of zero cupon bonds

        :param start: zero bond start date $t_0$
        :param stop: zero bond end date $t_1$
        :return: zero bond rate $z(t_0, t_1)$

        Assume a current price is $P(t_0, t_1)$ at time $t_0$
        of a zero cupon bond $P$ paying $1$ at maturity $t_1$
        without any interest or cupons.

        Such zero bond prices are used to
        give the price or present value $v_0(CF)$ at time $t_0$
        of any cashflow $CF$ at time $t_1$ by

        $$v_0(CF)
        = P(t_0, t_1) \cdot CF
        = \exp(-z(t_1-t_0) \cdot \tau(t_1-t_0)) \cdot CF$$

        where $\tau$ is the day count method to calculate the year fraction
        of the interest accrual period form $t_i$ to $t_{i+1}$
        given by |DateCurve().day_count()|.

        Note, this concept relates to the discount factor $df(t_0, t_1)$ of
        |InterestRateCurve().get_discount_factor()| by

        $$df(t_0, t_1) = \exp(-z(t_1-t_0) \cdot \tau(t_1 - t_0)).$$

        Note, this concept relates to short rates $df(t_0, t_1)$ of
        |InterestRateCurve().get_short_rate()| by

        $$z(t_0,t_1)(t_1-t_0) = \int_{t_0}^{t_1} r(t) dt.$$

        """
        start, stop = self._pre(start), self._pre(stop)
        return self.curve.zero(start, stop)

    def get_cash_rate(self, start, stop=None, step=None):
        r"""interbank cash lending rate

        :param start: start date of cash lending
        :param stop: end date of cash lending
            (optional; default **start** + **step**)
        :param step: period length of cash lending
            (optional; by default **step** is taken from
            |RateCurve().forward_tenor|)
        :return: simple compounded interest (forward) rate $f$

        Let **start** be $t_0$.
        If **step** and **stop** are given as $\tau$ and $t_1$
        then **start** + **step** = **stop** must meet such that
        $t_0 + \tau = t_1$ in

        $$f(t_0, t_1)=\frac{1}{\tau}\big(\frac{1}{df(t_0, t_1)}-1\big).$$

        Due to the `benchmark reform
        <https://www.isda.org/2022/05/16/benchmark-reform-and-transition-from-libor/>`_
        most classical cash rates as the *LIBOR* rates
        have been replaced by overnight rates,
        e.g. *SOFR*, *SONIA* etc.
        Derived from future prediictions of overnight rates
        (aka *short term* rates) long term rates with tenors of
        $1m$, $3m$, $6m$ and $12m$ are published, too.

        For classical term rates see
        `LIBOR <https://en.wikipedia.org/wiki/Libor>`_ and
        `EURIBOR <https://en.wikipedia.org/wiki/Euribor>`_,
        for overnight rates see
        `SOFR <https://en.wikipedia.org/wiki/SOFR>`_,
        `ESTR <https://en.wikipedia.org/wiki/ESTR>`_,
        `SONIA <https://en.wikipedia.org/wiki/SONIA>`_ and
        `SARON <https://en.wikipedia.org/wiki/SARON>`_ as well as
        `TONAR <https://en.wikipedia.org/wiki/TONAR>`_.

        """
        if step is None:
            step = getattr(self, 'forward_tenor', None) \
                   or getattr(self.__class__, 'forward_tenor', None)
        if stop is None and step is not None:
            stop = start + step
        start, stop = self._pre(start), self._pre(stop)
        return self.curve.cash(start, stop)

    def get_short_rate(self, start):
        r"""constant interpolated short rate derived from zero rate

        :param date start: point in time $t$ of short rate
        :return: short rate $r_t$ at given point in time

        Calculation assumes a zero rate derived
        from a interpolated short rate, i.e.

        Let $r_t=r(t)$ be the short rate on given time grid
        $t_0, t_1, \dots, t_n$ and
        let $z(s, t)$ be the zero rate from $s$ to $t$
        with $s, t \in \{t_0, t_1, \dots, t_n\}$.

        Hence,

        $$\int_s^t r(\tau) d\tau
        = \int_s^t c_s d\tau
        = \Big[c_s \tau \Big]_s^t
        = c_s(s-t)$$

        and so

        $$c_s = z(s, t).$$

        See also |InterestRateCurve().get_zero_rate()|.

        """
        start = self._pre(start)
        return self.curve.short(start)

    def get_swap_annuity(self, date_list=(), start=None, stop=None, step=None):
        r"""swap annuity as the accrual period weighted sum of discount factors

        :param date_list: list of period $t_0, \dots t_n$
        :return: swap annuity $A(t_0, \dots, t_n)$

        As

        $$A(t_0, \dots, t_n) = \sum_{i=1}^n df(0, t_i) \tau (t_i, t_{i+1})$$

        with

        * $0$ given by |DateCurve().origin|

        * $df$ discount factor given by
          |InterestRateCurve().get_discount_factor()|

        * $\tau $ day count method to calculate the year fraction
          of the interest accrual period form $t_i$ to $t_{i+1}$
          given by |DateCurve().day_count()|

        """
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


class FxApi(CurveAdapter):

    def get_fx_rate(self, value_date):
        """ forward exchange rate at **value_date**

        as the future price of one foreign currency unit.
        Derived by interpolation on given forward exchange rate
        and extrapolation by foreign and domestic interest rate curves.

        :param value_date: future date of exchange rate
        :return: forward exchange rate at **value_date**
        """
        value_date = self._pre(value_date)
        return self.curve.price(value_date)


class PriceApi(CurveAdapter):

    def get_forward_price(self, value_date):
        """ asset forward price at **value_date**

        derived by interpolation on given forward prices
        and extrapolation by given discount_factor resp. yield curve

        :param value_date: future date of asset price
        :return: asset forward price at **value_date**
        """
        value_date = self._pre(value_date)
        return self.curve.price(value_date)

    def get_price_yield(self, start, stop=None):
        """ asset yield between **start** and **stop** dates

        derived by interpolation on given forward prices
        and extrapolation by given discount_factor resp. yield curve

        :param start: date of start asset price
        :param stop: future date of stop asset price
        :return: asset return yield between **start** and **stop** dates
        """
        start, stop = self._pre(start), self._pre(stop)
        return self.curve.return_yield(start, stop)


class CreditApi(CurveAdapter):

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
        start, stop = self._pre(start), self._pre(stop)
        return self.curve.pd(start, stop)

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
        start, stop = self._pre(start), self._pre(stop)
        return self.curve.prob(start, stop)

    def get_marginal_prob(self, start):
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
        start = self._pre(start)
        return self.curve.marginal(start)

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
        start, stop = self._pre(start), self._pre(stop)
        return self.curve.intensity(start, stop)

    def get_hazard_rate(self, start):
        r"""hazard rate of credit curve

        :param start: point in time $t$ of hazard rate
        :return: hazard rate $hz(t)$

        The hazard rate $hz(t)$ relates to intensities by

        $$\lambda(t_0, t_1) = \int_{t_0}^{t_1} hz(t)\ dt.$$

        * similar to |InterestRateCurve().get_short_rate()|

        """
        start = self._pre(start)
        return self.curve.hazard_rate(start)


class VolApi(CurveAdapter):

    def get_terminal_vol(self, value_date):
        """terminal volatility at **value_date**

        :param value_date:
        :return:
        """
        value_date = self._pre(value_date)
        return self.curve(value_date)
