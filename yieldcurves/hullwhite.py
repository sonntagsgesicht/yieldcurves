# -*- coding: utf-8 -*-

# yieldcurves
# -----------
# A Python library for financial yield curves.
#
# Author:   sonntagsgesicht
# Version:  0.2.6.1, copyright Monday, 14 October 2024
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


from functools import cache
from math import sqrt, exp
from random import Random


from .compounding import continuous_compounding, continuous_rate
from .tools import ITERABLE
from .tools import init, integrate
from .tools import prettyclass
from .matrix import Matrix, Identity, cholesky


@prettyclass
class _HullWhiteModel:
    """Hull White model in terminal measure from sport rates"""
    random = Random()   # nosec B311

    def __init__(self, mean_reversion=0., volatility=0., terminal_date=1., *,
                 domestic=None, fx_volatility=0.,
                 domestic_correlation=0., fx_correlation=0.,
                 domestic_fx_correlation=0.):
        """

        >>> from yieldcurves import HullWhite
        >>> hw = HullWhite.Curve(0.02, mean_reversion=0.1, volatility=0.01)
        >>> hw.model.random.seed(101)

        >>> hw(2)
        0.020000...

        >>> hw.evolve(1)
        >>> hw(2)
        0.010080...

        >>> hw.evolve(2)
        >>> hw(2)
        0.005147...

        """

        if not isinstance(mean_reversion, float):
            mr_cls = mean_reversion.__class__.__name__
            msg = f'Mean reversion of type {mr_cls} not yet supported.' \
                  ' Please use float type.'
            raise NotImplementedError(msg)

        self.volatility = init(volatility)
        self.mean_reversion = float(mean_reversion)
        self.terminal_date = terminal_date

        # prepare for multi currency model
        if isinstance(domestic, _HullWhiteFactor):
            domestic = domestic.model
        self.domestic = domestic
        self.fx_volatility = init(fx_volatility)

        self.domestic_correlation = domestic_correlation
        self.fx_correlation = fx_correlation
        self.domestic_fx_correlation = domestic_fx_correlation

    def q(self, q=None):
        """fills list of correlated random numbers

        :param q: float or list of correlated random number
            q is domestic factor if it is a float or

            q[0] is domestic factor
            q[1] foreign factor
            q[2] fx factor

        :return: list of correlated random number with

            q[0] is domestic factor
            q[1] foreign factor
            q[2] fx factor

        """
        if isinstance(q, ITERABLE) and len(q) > 2:
            return q[:3]

        a = self.domestic_correlation
        b = self.fx_correlation
        c = self.domestic_fx_correlation
        # _corr = [[1, a, b], [a, 1, c], [b, c, 1]]
        d = sqrt(1 - a ** 2)
        e = (c - a * b) / d if d else 0.
        f = sqrt(1 - b ** 2 - e ** 2)
        # _cholesky = [[1, 0, 0], [a, d, 0], [b, e, f]]

        if q is None:
            q0 = self.random.gauss(0., 1.)
            q1 = self.random.gauss(0., 1.)
            q2 = self.random.gauss(0., 1.)
        elif isinstance(q, float):
            q0 = q
            q1 = self.random.gauss(0., 1.)
            q2 = self.random.gauss(0., 1.)
        elif len(q) == 1:
            q0 = q[0]  # domestic factor = domestic driver
            q1 = self.random.gauss(0., 1.)
            q2 = self.random.gauss(0., 1.)
        elif len(q) == 2:
            q0 = q[0]  # domestic factor = domestic driver
            q1 = (q[1] - a * q0) / d if d else q0  # foreign driver
            q2 = self.random.gauss(0., 1.)
        else:
            q0 = self.random.gauss(0., 1.)
            q1 = self.random.gauss(0., 1.)
            q2 = self.random.gauss(0., 1.)

        return q0, a * q0 + d * q1, b * q0 + e * q1 + f * q2

    # integration helpers for Hull White model

    def calc_integral_one(self, t1, t2):
        mr = self.mean_reversion
        return exp(-mr * (t2 - t1))

    def calc_integral_b(self, t1, t2):
        r"""returns the value of the helper function B

        $$B(t_1, t_2)
        = \int_{t_1}^{t_2} I_1(t_1, \tau)\, \mathrm{d}\tau
        = \frac{1}{a}\Big(1 - \mathrm{e}^{-a(t_2 - t_1)}\Big)$$
        """
        mr = self.mean_reversion or 1e-7
        return (1 - exp(- mr * (t2 - t1))) / mr

    @cache
    def calc_integral_two(self, t1, t2):
        r"""calculates integral of integrand I1 (aka integral two)

        $$\textrm{Var}_r(t_1,t_2)
        = \int_{t_1}^{t_2} vol(u)^2 I_1(u,t_2) \,\mathrm{d} u$$

        """
        calc_integral_one = self.calc_integral_one
        vol = self.volatility

        def func(x):
            return vol(x) ** 2 * calc_integral_one(x, t2)

        return integrate(func, t1, t2)

    @cache
    def calc_drift_integral(self, t1, t2):
        r"""value of the helper function Integrals

        One of the deterministic terms of a step
        in the MC simulation is calculated here
        with last observation date for T-Bond numeraire T

        $$\int_s^t \sigma^2(u) I_1(u,t) (B(u,t)-B(u,T)) \,\mathrm{d} u
        + B(s,t)I_1(s,t)\int_0^s \sigma^2(u) I_1^2(u,s)\,\mathrm{d}u$$

        """
        t_date = self.terminal_date
        d_vol = vol = self.volatility
        d_corr = 1.
        d_calc_integral_b = calc_integral_b = self.calc_integral_b
        calc_integral_one = self.calc_integral_one

        if self.domestic:
            d_vol = self.domestic.volatility
            d_corr = self.domestic_correlation
            d_calc_integral_b = self.domestic.calc_integral_b

        x_vol = self.fx_volatility
        x_corr = self.fx_correlation

        p3 = 0.
        if x_vol and x_corr:
            p3 = vol(t2) * x_vol(t2) * x_corr

        def func(u):
            p1 = vol(u) ** 2 * calc_integral_b(u, t2)
            p2 = vol(u) * d_vol(u) * d_calc_integral_b(u, t_date) * d_corr
            return calc_integral_one(u, t2) * (p1 - p2 - p3)

        part1and3 = integrate(func, t1, t2)
        part2 = self.calc_integral_b(t1, t2) * \
            self.calc_integral_one(t1, t2) * \
            self.calc_diffusion_integral(0., t1) ** 2

        return part1and3 + part2

    @cache
    def calc_diffusion_integral(self, t1, t2):
        """calculates diffusion integral"""
        calc_integral_one = self.calc_integral_one
        vol = self.volatility

        def func(x):
            return (vol(x) * calc_integral_one(x, t2)) ** 2

        return sqrt(integrate(func, t1, t2))

    def evolve_curve(self, t1, t2, x=0., q=None):
        self.calc_integral_two(0., t2)  # pre-calc for __call__
        i1 = self.calc_integral_one(t1, t2)
        i2 = self.calc_drift_integral(t1, t2)
        v = self.calc_diffusion_integral(t1, t2)
        q = self.random.gauss(0., 1.) if q is None else q
        return i1 * x + v * q + i2

    def curve(self, curve):
        return HullWhite.Curve(curve, model=self)

    # --- fx routines ---

    @cache
    def calc_fx_drift_integral(self, t1, t2):

        f_vol = self.volatility
        d_vol = (self.domestic or self).volatility
        vol = self.fx_volatility

        r_corr = self.domestic_correlation
        f_corr = self.fx_correlation
        d_corr = self.domestic_fx_correlation

        def func(u):
            p1 = vol(u) ** 2 + f_vol(u) ** 2 + d_vol(u) ** 2
            p4 = d_vol(u) * f_vol(u) * r_corr
            p5 = vol(u) * f_vol(u) * f_corr
            p6 = vol(u) * d_vol(u) * d_corr
            return p1 - p4 + p5 - p6

        return -0.5 * integrate(func, t1, t2)

    @cache
    def calc_fx_diffusion_integrals(self, t1, t2):
        domestic = self.domestic or self
        d_calc_integral_b = domestic.calc_integral_b
        d_vol = domestic.volatility

        def func(u):
            return -d_calc_integral_b(u, t2) * d_vol(u)

        part_d = integrate(func, t1, t2)

        f_calc_integral_b = self.calc_integral_b
        f_vol = self.volatility

        def func(u):
            return -f_calc_integral_b(u, t2) * f_vol(u)

        part_f = integrate(func, t1, t2)

        vol = self.fx_volatility
        part_x = integrate(vol, t1, t2)

        return part_d, part_x, part_f

    def evolve_fx(self, t1, t2, x=0., q=None):
        drift = self.calc_fx_drift_integral(t1, t2)
        v_d, v_x, v_f = self.calc_fx_diffusion_integrals(t1, t2)
        return x + drift - v_d * q[0] + v_f * q[1] + v_x * q[2]

    def fx(self, curve, domestic_curve=0.0, foreign_curve=0.0):
        if self.domestic is None:
            raise ValueError('multi currency models require domestic model')
        return HullWhite.Fx(curve, model=self,
                            domestic_curve=domestic_curve,
                            foreign_curve=foreign_curve)


@prettyclass
class _HullWhiteFactor(dict):

    @property
    def t(self):
        # current state / last entry
        return next(reversed(self)) if self else 0.0

    def __init__(self, curve, *, model=None, **kwargs):
        super().__init__()
        self.curve = init(curve)
        if model is None:
            model = HullWhite(**kwargs)
        self.model = model

    def evolve(self, step_size=.25, *, q=None):
        raise NotImplementedError("abstract method")

    def increments(self, n, *, step_size=None):
        if isinstance(n, int):
            if not step_size:
                step_size = self.model.terminal_date / n
            n = [t * step_size for t in range(1, n + 1)]
        return n

    def sample(self, n=4, *, step_size=None):
        n = self.increments(n, step_size=step_size)
        states = []
        past = self
        self_t = self.t
        for t in n:
            hw = self.__class__(self.curve, model=self.model)
            hw.update(past)
            hw.evolve(self_t + t - hw.t)
            states.append(hw)
            past = hw
        return states

    def simulate(self, k=1, n=4, *, step_size=None):
        n = self.increments(n, step_size=step_size)
        return [self.sample(n) for _ in range(k)]


class _HullWhiteCurve(_HullWhiteFactor):

    def __call__(self, x, y=None):
        if y is not None:
            return self(y) / self(x)
        t = self.t
        if not x:
            return self.curve(t)
        x += t  # todo: verify spot shift to t
        df = continuous_compounding(self.curve(x), x)
        df /= continuous_compounding(self.curve(t), t)
        b = self.model.calc_integral_b(t, x)
        a = exp(-0.5 * b ** 2 * self.model.calc_integral_two(0.0, t))
        return continuous_rate(df * a * exp(-b * self.get(t, 0.)), x)

    def evolve(self, step_size=.25, *, q=None):
        t = self.t
        x = t + step_size
        self[x] = self.model.evolve_curve(t, x, self.get(t, 0.), q)


class _HullWhiteFx(_HullWhiteFactor):

    def __init__(self, curve, *, model=None,
                 domestic_curve=0.0, foreign_curve=0.0, **kwargs):
        super().__init__(curve, model=model, **kwargs)
        if not callable(domestic_curve):
            domestic_curve = init(domestic_curve)
        self.domestic_curve = domestic_curve
        if not callable(foreign_curve):
            foreign_curve = init(foreign_curve)
        self.foreign_curve = foreign_curve

        if isinstance(self.domestic_curve, _HullWhiteFactor):
            if self.model.domestic is not self.domestic_curve.model:
                raise ValueError('domestic model does not match')
        if isinstance(self.foreign_curve, _HullWhiteFactor):
            if self.model is not self.foreign_curve.model:
                raise ValueError('model does not match')

    def __float__(self):
        t = self.t
        return self.curve(t) * exp(self.get(t, 0.))

    def __call__(self, x, y=None):
        if y is not None:
            return self(y) / self(x)
        # todo: verify spot shift to t, i.e. implied spot shift here
        df = continuous_compounding(self.domestic_curve(x), x)
        df /= continuous_compounding(self.foreign_curve(x), x)
        return float(self) * df

    def evolve(self, step_size=.25, *, q=None):
        t = self.t
        x = t + step_size
        self[x] = self.model.evolve_fx(t, x, self.get(t, 0.), q)


@prettyclass
class _HullWhiteGlobal:
    random = Random()  # nosec B311

    @staticmethod
    def foreign_correlation(rate_correlation=(), fx_correlation=(),
                            rate_fx_correlation=()):
        """builds big correlation matrix with index
            dom, fx_1, foreign_1, fx_2, foreign_2, ...

        :param rate_correlation: dom, foreign_1, foreign_2, ... (symmetric)
        :param fx_correlation: fx_1, fx_2, ... (symmetric)
        :param rate_fx_correlation:
            dom, foreign_1, foreign_2, ... vs. fx_1, fx_2, ... (non symmetric)
        :return: dom, foreign_1, fx_1, foreign_2, fx_2, ... (symmetric)

        >>> from yieldcurves import HullWhite

        >>> rate_corr = [
        ...    [1.0, 0.6, 0.8],
        ...    [0.6, 1.0, 0.7],
        ...    [0.8, 0.7, 1.0]
        ... ]
        >>> fx_corr = [
        ...    [1.0, 0.3],
        ...    [0.3, 1.0]
        ... ]
        >>> rate_fx_corr = [
        ...    [0.11, 0.12],
        ...    [0.21, 0.22],
        ...    [0.31, 0.32]
        ... ]

        >>> corr = HullWhite.Global.foreign_correlation(rate_corr, fx_corr, rate_fx_corr)
        >>> corr
        [[1.0, 0.6, 0.11, 0.8, 0.12],
         [0.6, 1.0, 0.21, 0.7, 0.22],
         [0.11, 0.21, 1.0, 0.31, 0.3],
         [0.8, 0.7, 0.31, 1.0, 0.32],
         [0.12, 0.22, 0.3, 0.32, 1.0]]

        """  # noqa E501
        # init correlation matrix
        #  dom, foreign_1, foreign_2, ..., fx_1, fx_2, ...
        dim = len(rate_correlation)
        correlation = Identity(dim + dim - 1)
        correlation[:dim, :dim] = Matrix(rate_correlation)
        correlation[1 - dim:, 1 - dim:] = Matrix(fx_correlation)

        c = Matrix(rate_fx_correlation)
        if c.shape == (dim - 1, dim):
            c = c.T
        correlation[:dim, 1 - dim:] = c
        correlation[1 - dim:, :dim] = c.T

        # sort index
        permutation = Identity(dim + dim - 1)
        #  dom, fx_1, foreign_1, fx_2, foreign_2, ...
        s = [i * 2 for i in range(dim)] + [j * 2 + 1 for j in range(dim - 1)]
        #  dom, foreign_1, fx_1, foreign_2, fx_2, ...
        s = [0] + [i * 2 + 1 for i in range(dim - 1)] + \
            [j * 2 + 2 for j in range(dim - 1)]
        permutation[:, :] = permutation[:, s]

        return (permutation @ correlation @ permutation.T).tolist()

    @staticmethod
    def foreign_factors(curves, fx=(), *,
                        mean_reversion=(), volatility=(), terminal_date=1.,
                        domestic=None, fx_volatility=()):
        """builds list of HullWhite factors (curve + optional fx)

        :param curves: list of yield curves
        :param fx: list of fx rates (optional: default are 1. fx factors)
        :param mean_reversion: list of mean_reversion values
            (optional: defaults to HullWhite defaults)
        :param volatility: list of rate volatility values
            (optional: defaults to HullWhite defaults)
        :param terminal_date: date of terminal measure
            (optional: defaults to HullWhite defaults)
        :param domestic: domestic HullWhite curve or None
        :param fx_volatility: list of fx volatility values
            (optional: defaults to HullWhite defaults)
        :return: list of HullWhite curves and - if given - fx

        >>> from yieldcurves import HullWhite

        >>> curves = 0.02, 0.03
        >>> fx_rates = 1.2, 2.3

        >>> mean_reversion = 0.12, 0.21
        >>> volatility = 0.06, 0.07
        >>> fx_volatility = 0.1, 0.2

        first init domestic HullWhite curve

        >>> domestic = HullWhite(0.1, 0.04).curve(0.01)

        then build foreign HullWhite curves and HullWhite fx ractors

        >>> factors = HullWhite.Global.build_factors(curves, fx=fx_rates,
        ... mean_reversion=mean_reversion, volatility=volatility,
        ... domestic=domestic, fx_volatility=())
        >>> factors
        [HullWhite.Curve(0.02, model=HullWhite(0.12, 0.06, domestic=HullWhite(0.1, 0.04))),
         HullWhite.Fx(1.2, model=HullWhite(0.12, 0.06, domestic=HullWhite(0.1, 0.04))),
         HullWhite.Curve(0.03, model=HullWhite(0.21, 0.07, domestic=HullWhite(0.1, 0.04))),
         HullWhite.Fx(2.3, model=HullWhite(0.21, 0.07, domestic=HullWhite(0.1, 0.04)))]

        """  # noqa E501
        domestic_curve = None
        if isinstance(domestic, _HullWhiteCurve):
            domestic_curve = domestic
        if isinstance(domestic, _HullWhiteFactor):
            domestic = domestic.model

        # prep to make parameters optional with defaults
        mean_reversion = dict(zip(range(len(mean_reversion)), mean_reversion))
        volatility = dict(zip(range(len(volatility)), volatility))
        fx_volatility = dict(zip(range(len(fx_volatility)), fx_volatility))
        fx = fx if fx is None else dict(zip(range(len(fx)), fx))

        # build curve factors
        factors = []
        default = HullWhite()
        for i, c in enumerate(curves):
            # make parameters optional with defaults
            mr = mean_reversion.get(i, default.mean_reversion)
            vol = volatility.get(i, default.volatility)
            fx_vol = fx_volatility.get(i, default.fx_volatility)
            model = HullWhite(mr, vol, terminal_date=terminal_date,
                              domestic=domestic, fx_volatility=fx_vol)
            foreign_curve = model.curve(c)
            factors.append(foreign_curve)
            if fx is not None:  # add fx if given
                if domestic_curve is not None:
                    fx_curve = model.fx(fx.get(i, 1.),
                                        domestic_curve=domestic_curve,
                                        foreign_curve=foreign_curve)
                else:
                    fx_curve = model.fx(fx.get(i, 1.))
                factors.append(fx_curve)
        return factors

    @classmethod
    def from_parameters(cls, curves, fx=(), *,
                        mean_reversion=(), volatility=(), terminal_date=1.,
                        domestic=None, fx_volatility=(), correlation=None):
        """init global HullWhite model from factor parameters

            mostly same as HullWhite.Global.build_factors
            but uses first items to construct domestic HullWhite curve
            if not given explicit

        """
        # setup domestic model and curve
        if domestic is None:
            c = mr = vol = 0.0
            if len(mean_reversion):
                mr, *mean_reversion = mean_reversion
            if len(volatility):
                vol, *volatility = volatility
            if len(curves):
                c, *curves = curves
            domestic = HullWhite(mr, vol, terminal_date=terminal_date).curve(c)
        factors = cls.foreign_factors(curves, fx=fx,
                                      mean_reversion=mean_reversion,
                                      volatility=volatility,
                                      terminal_date=terminal_date,
                                      domestic=domestic,
                                      fx_volatility=fx_volatility)
        return cls([domestic] + factors, correlation=correlation)

    def __init__(self, factors, correlation=None):
        """init global HullWhite model from factors and correlation

        :param factors:
        :param correlation:

        >>> from yieldcurves import HullWhite

        >>> rate_corr = [[1.0, 0.6], [0.6, 1.0]]
        >>> fx_corr = [[1.0]]
        >>> rate_fx_corr = [[0.22], [0.33]]
        >>> corr = HullWhite.Global.foreign_correlation(rate_corr, fx_corr, rate_fx_corr)

        >>> domestic = HullWhite(0.1, 0.05).curve(0.02)
        >>> foreign =  HullWhite(0.2, 0.02, domestic=domestic, fx_volatility=0.2).curve(0.05)
        >>> fx = foreign.model.fx(2.2)

        >>> g = HullWhite.Global([domestic, foreign, fx], correlation=corr)

        >>> d, f, x = g.factors
        >>> d(.5), f(.5), d(1.5), f(1.5), float(x)
        (0.019999..., 0.050000..., 0.020000..., 0.050000..., 2.2)

        >>> g.evolve()
        >>> dict(f.items())
        {0.25: 0.008438...}

        >>> d(.5), f(.5), d(1.5), f(1.5), float(x)
        (0.048727..., 0.038701..., 0.060689..., 0.049152..., 2.089911...)

        >>> g.evolve()
        >>> dict(f.items())
        {0.25: 0.008438..., 0.5: 0.010379...}

        >>> d(.5), f(.5), d(1.5), f(1.5), float(x)
        (0.039533..., 0.029960..., 0.057559..., 0.044305..., 2.161724...)

        >>> g.clear()
        >>> dict(f.items())
        {}

        >>> d(.5), f(.5), d(1.5), f(1.5), float(x)
        (0.019999..., 0.050000..., 0.020000..., 0.050000..., 2.2)

        """  # noqa E501

        self.factors = factors
        self.correlation = correlation

        if correlation:
            if not len(factors) == len(correlation):
                msg = f"correlation of wrong size {len(correlation)}" \
                      f" expected size {len(factors)}"
                raise ValueError(msg)

        if factors:
            # set first factor as domestic
            domestic, *factors = factors

            # validate domestic
            if domestic.model.domestic is not None:
                msg = f"domestic model must not have domestic model {domestic}"
                raise ValueError(msg)

            # validate model order
            for i in range(0, len(factors), 2):
                if not isinstance(factors[i], _HullWhiteCurve):
                    cls = factors[i].__class__.__qualname__
                    msg = f'curve factor {i} of wrong type: {cls}'
                    raise ValueError(msg)
                if not isinstance(factors[i + 1], _HullWhiteFx):
                    cls = factors[i].__class__.__qualname__
                    raise ValueError(f'fx factor {i + 1} of wrong type: {cls}')
                if factors[i].model is not factors[i + 1].model:
                    raise ValueError(f'factor model {i}  and {i + 1} differ')
                if factors[i].model.domestic is not domestic.model:
                    d = factors[i].model.domestic
                    msg = f"domestic factor model {str(d)!r}" \
                          f" differs from {str(domestic.model)!r}"
                    raise ValueError(msg)

    @cache
    def cholesky(self, h):
        correlation = self.correlation

        if not str(correlation) == h:
            msg = f"expected different correlation\n{h}\nvs\n{correlation}"
            raise RuntimeError(msg)

        if correlation is None:
            return None

        if not len(self.factors) == len(correlation):
            msg = f"correlation of wrong size {len(correlation)}" \
                  f" expected {len(self.factors)}"
            raise ValueError(msg)

        # set correlation in models
        for i in range(1, len(self.factors), 2):
            m = self.factors[i].model
            m.domestic_correlation = correlation[0][i]
            m.fx_correlation = correlation[i][i - 1]
            m.domestic_fx_correlation = correlation[0][i - 1]

        return cholesky(correlation, lower=True)

    @property
    def domestic(self):
        return self.factors[0] if self.factors else None

    @property
    def t(self):
        return self.domestic.t if self.domestic else None

    def evolve(self, step_size=.25):
        if not self.factors:
            return
        random = self.factors[0].model.random
        c = self.cholesky(str(self.correlation))  # hack to use @cache
        q = [random.gauss(0., 1.) for _ in range(len(self.factors))]
        if c is not None:
            q = list(map(float, c.dot(q)))
        for i, f in enumerate(self.factors):
            if isinstance(f, _HullWhiteCurve):
                f.evolve(step_size, q=q[i])
            elif isinstance(f, _HullWhiteFx):
                f.evolve(step_size, q=[q[0], q[i - 1], q[i]])
            else:
                raise TypeError(f"cannot evolve {f.__class__.__qualname__}")

    def clear(self):
        for f in self.factors:
            f.clear()

    def update(self, other):
        if isinstance(other, _HullWhiteGlobal):
            for f, p in zip(self.factors, other.factors):
                f.update(p)
        for f in self.factors:
            f.update(other)

    def sample(self, n=4, *, step_size=None):
        n = self.factors[0].increments(n, step_size=step_size)
        states = []
        past = self
        self_t = self.t
        for t in n:
            hw = self.__class__(self.factors, correlation=self.correlation)
            hw.update(past)
            hw.evolve(self_t + t - hw.t)
            states.append(hw)
            past = hw
        return states

    def simulate(self, k=1, n=4, *, step_size=None):
        n = self.factors[0].increments(n, step_size=step_size)
        return [self.sample(n) for _ in range(k)]


class HullWhite(_HullWhiteModel):

    class Curve(_HullWhiteCurve):
        ...

    class Fx(_HullWhiteFx):
        ...

    class Global(_HullWhiteGlobal):
        ...
