
from .. import interpolation as _interpolation
from ..curve import CurveAdapter
from ..daycount import YearFraction
from ..interpolation import linear
from ..analytics.rate import ZeroRateAdapter, DiscountFactorAdapter, \
    ShortRateAdapter, CashRateAdapter


class RateCurve(CurveAdapter):

    forward_tenor = None

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
        domain = tuple(domain)

        # build yf transformer, transform domain and build inner curve
        yf = YearFraction(origin, day_count, domain=domain)
        i_type = getattr(_interpolation, str(interpolation), interpolation)
        super().__init__(i_type(yf(domain), data), pre=yf, inv=yf.inv)

        # save properties
        self.domain = domain
        self.origin = origin
        self.day_count = day_count
        self.interpolation = getattr(i_type, '__name__', str(interpolation))

        self.forward_tenor = forward_tenor
        frequency = 1 / self._pre(self.origin + self.forward_tenor)
        curve_type = str(self.__class__.__name__).lower()
        if curve_type.startswith('zero'):
            adapter = ZeroRateAdapter(self.curve, frequency=frequency)
        elif curve_type.startswith('short'):
            adapter = ShortRateAdapter(self.curve, frequency=frequency)
        elif curve_type.startswith('cash'):
            adapter = CashRateAdapter(self.curve, frequency=frequency)
        elif curve_type.startswith('df') or 'df' in curve_type:
            adapter = DiscountFactorAdapter(self.curve, frequency=frequency)
        else:
            raise NotImplementedError(f'unknown curve type {curve_type}')
        self.adapter = adapter

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
        return self.adapter.df(start, stop)

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
        return self.adapter.zero(start, stop)

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
        if not self.adapter.frequency and step is None:
            step = getattr(self, 'forward_tenor', None) \
                   or self.__class__.forward_tenor
        if stop is None and step is not None:
            stop = start + step
        start, stop = self._pre(start), self._pre(stop)
        return self.adapter.cash(start, stop)

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
        return self.adapter.short(start)

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


ZeroRateCurve = type('ZeroRateCurve', (RateCurve,), {})
ShortRateCurve = type('ShortRateCurve', (RateCurve,), {})
CashRateCurve = type('CashRateCurve', (RateCurve,), {})
DiscountFactorCurve = type('DiscountFactorCurve', (RateCurve,), {})
