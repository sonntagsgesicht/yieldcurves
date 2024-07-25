# -*- coding: utf-8 -*-

# shortrate
# ---------
# risk factor model library python style.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.3, copyright Wednesday, 18 September 2019
# Website:  https://github.com/sonntagsgesicht/shortrate
# License:  Apache License 2.0 (see LICENSE file)


from math import exp
from random import Random

from scipy import integrate
from scipy.linalg import cholesky

from ..yieldcurves import _const

from .hullwhite_model import HullWhite, calc_integral_B, calc_integral_one
from .gbm_model import GBM


class HullWhiteMultiCurrency(HullWhite):
    """
        build HullWhiteMultiCurrencyCurve from HullWhiteCurves and HullWhiteFxCurve.
        Terminal measure date in foreign is ignored since it is taken from domestic.
        initializes foreign Hull White drift in multi currency model
    """

    def __init__(self, curve, *, domestic, fx_volatility=0.,
                 domestic_correlation=0., fx_correlation=0.,
                 mean_reversion=0., volatility=0.):
        if not isinstance(domestic, HullWhite):
            msg = f"{self.__class__.__name__} requires domestic curve " \
                  f"of type {HullWhite.__name__} " \
                  f"but {domestic.__class__.__name__} is given."
            raise TypeError(msg)

        if isinstance(curve, HullWhite):
            mean_reversion = curve.mean_reversion
            volatiliy = curve.volatility

        super(HullWhiteMultiCurrency, self).__init__(
            curve, mean_reversion=mean_reversion, volatility=volatility,
            step_size=domestic.step_size, terminal_date=domestic.terminal_date)

        # collect parameter for multi currency Hull White model
        self.domestic = domestic
        self.fx_volatility = \
            fx_volatility if callable(fx_volatility) else _const(fx_volatility)
        self.domestic_correlation = domestic_correlation
        self.fx_correlation = fx_correlation

    def calc_integral_I2(self, s, t):
        r"""calculates the following integral

        $$\textrm{Var}(\chi(t) | \mathcal{F}_s)
        = \int_s^t \sigma^2_d(u)B^2_d(u, T)
        + \sigma^2_f(u)B^2_f(u,T) + \sigma^2_{FX}(u) \\
        + 2\left(- \rho_{d,f} B_f(u, T)\sigma_f(u)B_d(u, T)\sigma_d(u)
        + \left( - \rho_{f,FX} B_f(u, T)\sigma_f(u)
        + \rho_{d,FX} B_d(u, T)\sigma_d(u) \right)
        \sigma_{FX}(u) \right)\,\mathrm{d}u$$

        (see formula for the step in the MC evolution)

        """

        T = self.terminal_date
        mr = self.mean_reversion
        vol = self.volatility

        d_mr = self.domestic.mean_reversion
        d_vol = self.domestic.volatility
        d_corr = self.domestic_correlation

        fx_vol = self.fx_volatility
        fx_corr = self.fx_correlation

        if not fx_corr and not d_corr:
            return super(HullWhiteMultiCurrency, self).calc_integral_I2(s, t)

        p3 = fx_corr * vol(t) * fx_vol(t)

        def func(u):
            p1 = vol(u) ** 2 * calc_integral_B(u, t, mr)
            p2 = d_corr * vol(u) * d_vol(u) * calc_integral_B(u, T, d_mr)
            return calc_integral_one(u, t, mr) * (p1 - p2 - p3)

        part1, *_ = integrate.quad(func, s, t)
        part2 = calc_integral_B(s, t, mr) * \
                calc_integral_one(s, t, mr) * \
                self.calc_integral_volatility_squared_with_I1_squared(0., s)

        return part1 + part2


class HullWhiteFx:

    def __init__(self, curve, *, domestic, foreign, volatility=0.0,
                 domestic_correlation=0., foreign_correlation=0.,
                 rate_correlation=0.):
        """

        :param float curve: fx rate
        :param HullWhite domestic:
        :param HullWhite foreign:
        :param float: volatility
            (optional) Default: either inner_factor.volatility or 0.0
        :param float domestic_correlation:
            (optional) Default: 0.0
        :param float foreign_correlation:
            (optional) Default: 0.0
        :param float rate_correlation:
            (optional) Default: 0.0
        :param dict((RiskFactorModel, RiskFactorModel), float) correlation
            (optional) Default: explicit given correlations

        """
        if not isinstance(curve, float):
            msg = f"{self.__class__.__name__} requires curve " \
                  f"of type {float.__name__}" \
                  f"but {curve.__class__.__name__} is given"
            raise TypeError(msg)

        if not isinstance(domestic, HullWhite):
            msg = f"{self.__class__.__name__} requires domestic " \
                  f"of type {HullWhite.__name__}" \
                  f"but {domestic.__class__.__name__} is given"
            raise TypeError(msg)

        if not isinstance(foreign, HullWhite):
            msg = f"{self.__class__.__name__} requires foreign " \
                  f"of type {HullWhite.__name__}" \
                  f"but {foreign.__class__.__name__} is given"
            raise TypeError(msg)

        self.curve = curve if callable(curve) else _const(curve)
        self.domestic = domestic
        self.foreign = foreign

        # todo:
        #   self.volatility = getattr(curve, 'volatility', _const(volatility))
        self.volatility = \
            volatility if callable(volatility) else _const(volatility)

        self.domestic_correlation = domestic_correlation
        self.foreign_correlation = foreign_correlation
        self.rate_correlation = rate_correlation

        self._corr = self._cholesky = None

        # init random
        self.random = Random()
        self.state = {0.0: 1.0}

        self._pre_calc_drift = dict()
        self._pre_calc_diffusion = dict()

    def _cholesky(self):
        _corr = self.domestic_correlation, \
            self.foreign_correlation, self.rate_correlation
        if self._cholesky and self._corr == _corr:
            return self._cholesky

        self._corr = _corr
        c = self._cholesky = cholesky(
            [[1, self.domestic_correlation, self.rate_correlation],
             [self.domestic_correlation, 1, self.foreign_correlation],
             [self.rate_correlation, self.foreign_correlation, 1]]
        )
        return c

    # integrate drift and diffusion integrals

    def _calc_drift_integrals(self, s, e):

        if (s, e) in self._pre_calc_drift:
            return self._pre_calc_drift[s, e]

        vol = self.volatility
        d_mr = self.domestic.mean_reversion
        d_vol = self.domestic.volatility
        f_mr = self.foreign.mean_reversion
        f_vol = self.foreign.volatility

        d_corr = self.domestic_correlation
        f_corr = self.foreign_correlation
        r_corr = self.rate_correlation

        def func(u):
            p1 = vol(u) ** 2 + f_vol(u) ** 2 + d_vol(u) ** 2
            p4 = d_vol(u) * f_vol(u) * r_corr
            p5 = vol(u) * f_vol(u) * f_corr
            p6 = vol(u) * d_vol(u) * d_corr
            return p1 - p4 + p5 - p6

        part, *_ = integrate.quad(func, s, e)
        self._pre_calc_drift[s, e] = -0.5 * part
        return -0.5 * part

    def _calc_diffusion_integrals(self, s, e):

        if (s, e) in self._pre_calc_diffusion:
            return self._pre_calc_diffusion[s, e]

        d_mr = self.domestic.mean_reversion
        d_vol = self.domestic.volatility
        f_mr = self.foreign.mean_reversion
        f_vol = self.foreign.volatility

        func = (lambda u: -calc_integral_B(u, e, d_mr) * d_vol(u))
        part_d, *_ = integrate.quad(func, s, e)

        func = (lambda u: -calc_integral_B(u, e, f_mr) * f_vol(u))
        part_f, *_ = integrate.quad(func, s, e)

        part_x, *_ = integrate.quad(self.volatility, s, e)
        self._pre_calc_diffusion[s, e] = part_d, part_x, part_f
        return part_d, part_x, part_f

    # risk factor methods

    def evolve(self, step_size=None, q=None):
        r"""evolve Hull White process of shortrate deviation and
        set risk factor and prepare discount factor integral

        set $y=r(t)-F(0,t)$ risk factor and prepare discount factor integral
        $$\int_0^t \sigma(u)^2 I_1(u, t) du$$

        """
        step_size = step_size or self.domestic.step_size
        s = next(reversed(self.state))  # current state / last entry
        e = s + step_size
        d = self._calc_drift_integrals(s, e)
        v_d, v_x, v_f = self._calc_diffusion_integrals(s, e)

        if q is None:
            c = self._cholesky()
            q = [self.random.gauss(0., 1.) for _ in range(len(c))]
            q = list(c.dot(q))

        x = self.state[s]
        y = self.state[e] = x * exp(d - v_d * q[0] + v_x * q[1] + v_f * q[2])
        return y

    def reset(self, e=0.0):
        self.state = {k: v for k, v in self.state.items() if k <= e}
        self._pre_calc_drift = {}
        self._pre_calc_diffusion = {}
        return self

    # curve methods

    def __call__(self, x, y=None):
        if y is not None:
            msg = f"y argument must not be set in {self.__class__.__name__}"
            raise TypeError(msg)
        r = self.foreign(x) - self.domestic(x)
        # return self.curve(x) * continuous_compounding(r, x)
        s = next(reversed(self.state))  # current state / last entry
        return self.state[s]
