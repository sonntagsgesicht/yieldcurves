# -*- coding: utf-8 -*-

# shortrate
# ---------
# risk factor model library python style.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.3, copyright Wednesday, 18 September 2019
# Website:  https://github.com/sonntagsgesicht/shortrate
# License:  Apache License 2.0 (see LICENSE file)


from math import sqrt, exp
from random import Random

from scipy import integrate

from ..compounding import continuous_compounding, continuous_rate
from ..yieldcurves import _const


def calc_integral_one(t1, t2, mr):
    r"""value of the helper function I1

    $$I_1(t_1, t_2)
    = \exp \left( -\int_{t_1}^{t_2} a(\tau) \,\mathrm{d}\tau \right)
    = \mathrm{e}^{-a(t_2 - t_1)}$$

    """
    mr = max(mr, 1e-7)
    return exp(-mr * (t2 - t1))


def calc_integral_B(t1, t2, mr=None):
    r"""returns the value of the helper function B

    $$B(t_1, t_2)
    = \int_{t_1}^{t_2} I_1(t_1, \tau)\, \mathrm{d}\tau
    = \frac{1}{a}\Big(1 - \mathrm{e}^{-a(t_2 - t_1)}\Big)$$
    """
    mr = max(mr, 1e-7)
    return (1 - exp(- mr * (t2 - t1))) / mr


class HullWhite:
    """Hull White model in terminal measure from sport rates"""

    def __init__(self, curve, *, mean_reversion=0.0, volatility=0.0,
                 step_size=0.25, terminal_date=1.0):
        """

        :param curve: callable
        :param mean_reversion: float
        :param volatility: float or callable
        :param terminal_date: float

        >>> from yieldcurves.shortrate import HullWhite
        >>> hw = HullWhite(0.02, mean_reversion=0.1, volatility=0.01)

        >>> hw(2)
        0.02

        >>> hw.evolve(1)
        >>> hw(2)
        0.02

        >>> hw.evolve(2)
        >>> hw(2)
        0.02
        """

        if not isinstance(mean_reversion, float):
            mr_cls = mean_reversion.__class__.__name__
            msg = f'Mean reversion of type {mr_cls} not yet supported.'\
                  ' Please use float type.'
            raise NotImplementedError(msg)

        self.curve = curve if callable(curve) else _const(curve)
        self.volatility = \
            volatility if callable(volatility) else _const(volatility)
        self.mean_reversion = float(mean_reversion)
        self.step_size = step_size
        self.terminal_date = terminal_date

        # init random
        self.random = Random()
        self.state = {0.0: 0.0}

        # init integration caches
        self._pre_calc_diffusion = {}
        self._pre_calc_drift = {}
        self._integral_vol_squared_I1 = {}

    # integration helpers for Hull White model

    def calc_integral_I1(self, t1, t2):
        r"""value of the helper function I1

        $$I_1(t_1, t_2)
        = \exp \left( -\int_{t_1}^{t_2} a(\tau) \,\mathrm{d}\tau \right)
        = \mathrm{e}^{-a(t_2 - t_1)}$$

        """
        return calc_integral_one(t1, t2, self.mean_reversion)

    def calc_integral_B(self, t1, t2):
        r"""returns the value of the helper function B

        $$B(t_1, t_2)
        = \int_{t_1}^{t_2} I_1(t_1, \tau)\, \mathrm{d}\tau
        = \frac{1}{a}\Big(1 - \mathrm{e}^{-a(t_2 - t_1)}\Big)$$
        """
        return calc_integral_B(t1, t2, self.mean_reversion)

    def calc_integral_volatility_squared_with_I1(self, t1, t2):
        """calculates integral of integrand I1

        $$\textrm{Var}_r(t_1,t_2)
        = \int_{t_1}^{t_2} vol(u)^2 I_1(u,t_2) \,\mathrm{d} u$$

        """
        mr = self.mean_reversion
        vol = self.volatility
        def func(x):
            return vol(x) ** 2 * calc_integral_one(x, t2, mr)
        result, *_ = integrate.quad(func, t1, t2)
        return result

    def calc_integral_volatility_squared_with_I1_squared(self, t1, t2):
        """calculates drift integral two"""
        # func = (lambda x: self.volatility(x) ** 2 * \
        #         self.calc_integral_I1_squared(x, t2))
        mr = self.mean_reversion
        vol = self.volatility
        def func(x):
            return vol(x) ** 2 * exp(-2.0 * mr * (t2 - t1))
        result, *_ = integrate.quad(func, t1, t2)
        return result

    def calc_integral_I2(self, s, t):
        r"""value of the helper function Integrals

        One of the deterministic terms of a step in the MC simulation is calculated here
        with last observation date for T-Bond numeraire T

        $$\int_s^t \sigma^2(u) I_1(u,t) (B(u,t)-B(u,T)) \,\mathrm{d} u
        + B(s,t)I_1(s,t)\int_0^s \sigma^2(u) I_1^2(u,s)\,\mathrm{d}u$$

        """
        T = self.terminal_date
        mr = self.mean_reversion
        vol = self.volatility
        def func(u):
            v = vol(u) ** 2 * calc_integral_one(u, t, mr)
            v *= calc_integral_B(u, t, mr) - calc_integral_B(u, T, mr)
            return v
        part1and3, *_ = integrate.quad(func, s, t)
        part2 = calc_integral_B(s, t, mr) * calc_integral_one(s, t, mr) * \
            self.calc_integral_volatility_squared_with_I1_squared(0., s)
        return part1and3 + part2

    # integrate drift integrals of drift part

    def _calc_integrals(self, e):
        r"""method to precalculate $ \int_0^t \sigma(u)^2 I_1(u, t) du$ """
        if e in self._integral_vol_squared_I1:
            return self._integral_vol_squared_I1[e]
        v = self.calc_integral_volatility_squared_with_I1(0.0, e)
        self._integral_vol_squared_I1[e] = v
        return v

    # integrate drift and diffusion integrals of stochastic process part

    def _calc_drift_integrals(self, s, e):
        """method to precalculate drift integrals"""
        if (s, e) in self._pre_calc_drift:
            return self._pre_calc_drift[s, e]
        i1 = calc_integral_one(s, e, self.mean_reversion)
        i2 = self.calc_integral_I2(s, e)
        self._pre_calc_drift[s, e] = i1, i2
        return i1, i2

    def _calc_diffusion_integrals(self, s, e):
        """method to precalculate diffusion integrals"""
        if (s, e) in self._pre_calc_diffusion:
            return self._pre_calc_diffusion[s, e]
        var = self.calc_integral_volatility_squared_with_I1_squared(s, e)
        sqrt_var = sqrt(var)
        self._pre_calc_diffusion[s, e] = sqrt_var
        return sqrt_var

    # risk factor methods

    def evolve(self, step_size=None, q=None):
        r"""evolve Hull White process of shortrate deviation and
        set risk factor and prepare discount factor integral

        set $y=r(t)-F(0,t)$ risk factor and prepare discount factor integral
        $$\int_0^t \sigma(u)^2 I_1(u, t) du$$

        """
        s = next(reversed(self.state))  # current state / last entry
        e = s + (step_size or self.step_size)
        self._calc_integrals(e)
        i1, i2 = self._calc_drift_integrals(s, e)
        v = self._calc_diffusion_integrals(s, e)

        if q is None:
            q = self.random.gauss(0., 1.)

        x = self.state[s]
        y = self.state[e] = x * i1 + i2 + v * q
        return y

    def reset(self, e=0.0):
        self.state = {k: v for k, v in self.state.items() if k <= e}
        self._pre_calc_drift = {}
        self._pre_calc_diffusion = {}
        self._integral_vol_squared_I1 = {}
        return self

    # curve methods

    def __call__(self, x, y=None):
        r"""calculate the spot rate for the given start date and end date

        $$(s,t) \mapsto P_{\text{init}}(s,t) \exp
        \left(-\frac{1}{2}(B^2(u,t)-B^2(u,s))
        \int_0^u \sigma^2(\tau)I_1(\tau,t),
        \mathrm{d}\tau\right)\mathrm{e}^{-(B(t,T)-B(t,S))y}$$

        with $P_{\text{init}}(s,t) = \verb|Curve.get_discount_curve(s,t)|$

        """
        if y is None:
            x, y = 0, x
        # todo: requires yf <= x, y ?
        yf = next(reversed(self.state))  # current state / last entry
        v = self.state[yf]
        mr = self.mean_reversion
        s = calc_integral_B(yf, x, mr)
        e = calc_integral_B(yf, y, mr)

        df = continuous_compounding(self.curve(x), x)
        df /= continuous_compounding(self.curve(y), y)
        df *= exp((s - e) * (0.5 * (s + e) * self._calc_integrals(yf) + v))
        return continuous_rate(df, y - x)
