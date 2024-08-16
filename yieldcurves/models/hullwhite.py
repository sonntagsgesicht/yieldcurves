from functools import cache
from math import sqrt, exp
from random import Random

from ..compounding import continuous_compounding, continuous_rate
from ..tools import integrate
from ..tools.pp import pretty
from ..tools.constant import init
from ..tools.matrix import Matrix, Identity, cholesky


@pretty
class _HullWhiteModel:
    """Hull White model in terminal measure from sport rates"""
    random = Random()

    def __init__(self, mean_reversion=0., volatility=0., terminal_date=1., *,
                 domestic=None, fx_volatility=0.,
                 domestic_correlation=0., fx_correlation=0.,
                 domestic_fx_correlation=0.):
        """

        >>> from yieldcurves.models import HullWhite
        >>> hw = HullWhite.Curve(0.02, mean_reversion=0.1, volatility=0.01)

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
            msg = f'Mean reversion of type {mr_cls} not yet supported.' \
                  ' Please use float type.'
            raise NotImplementedError(msg)

        self.volatility = init(volatility)
        self.mean_reversion = float(mean_reversion)
        self.terminal_date = terminal_date

        # prepare for multi currency model
        self.domestic = domestic
        self.fx_volatility = init(fx_volatility)

        self.domestic_correlation = domestic_correlation
        self.fx_correlation = fx_correlation
        self.domestic_fx_correlation = domestic_fx_correlation

    @staticmethod
    @cache
    def cholesky(domestic_rate, domestic_fx, rate_fx):
        if domestic_rate == 1. and not any((domestic_fx, rate_fx)):
            return None
        corr = [
            [1., domestic_fx, domestic_rate],
            [domestic_fx, 1., rate_fx],
            [domestic_rate, rate_fx, 1.]
        ]
        return cholesky(corr, lower=True)

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
        """calculates integral of integrand I1 (aka integral two)

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

        One of the deterministic terms of a step in the MC simulation is calculated here
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

    def evolve(self, t1, t2, x=0., q=None):
        self.calc_integral_two(0., t2)  # pre-calc for __call__
        i1 = self.calc_integral_one(t1, t2)
        i2 = self.calc_drift_integral(t1, t2)
        v = self.calc_diffusion_integral(t1, t2)
        q = self.random.gauss(0., 1.) if q is None else q
        return i1 * x + v * q + i2

    def increments(self, n, *, step_size=None):
        if isinstance(n, int):
            if not step_size:
                step_size = self.terminal_date / n
            n = [t * step_size for t in range(1, n + 1)]
        return n

    def sample(self, n=4, *, step_size=None):
        n = self.increments(n, step_size=step_size)
        states = []
        s = x = 0.
        for e in n:
            x = self.evolve(s, e, x)
            states.append(x)
            s = e
        return states

    def simulate(self, k=1, n=4, *, step_size=None):
        n = self.increments(n, step_size=step_size)
        return [self.sample(n) for _ in range(k)]

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
        d = self.calc_fx_drift_integral(t1, t2)
        v_d, v_x, v_f = self.calc_fx_diffusion_integrals(t1, t2)
        if q is None:
            c = self.cholesky(self.domestic_correlation,
                              self.domestic_fx_correlation,
                              self.fx_correlation)
            q = [self.random.gauss(0., 1.) for _ in range(3)]
            q = list(c.dot(q)) if c is not None else q
        return x + d - v_d * q[0] + v_x * q[1] + v_f * q[2]

    def fx(self, curve):
        if self.domestic is None:
            raise ValueError('multi currency models require domestic model')
        return HullWhite.Fx(curve, model=self)


@pretty
class _HullWhiteFactor(dict):

    @property
    def t(self):
        # current state / last entry
        return next(reversed(self)) if self else 0.0

    def __init__(self, curve, *, model=None, **kwargs):
        super().__init__()
        self.curve = init(curve)
        self.model = HullWhite(**kwargs) if model is None else model

    def evolve(self, step_size=.25, q=None):
        t = self.t
        x = t + step_size
        self[x] = self.model.evolve(t, x, self.get(t, 0.), q)

    def sample(self, n=4, *, step_size=None):
        n = self.model.increments(n, step_size=step_size)
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
        n = self.model.increments(n, step_size=step_size)
        return [self.sample(n) for _ in range(k)]


class _HullWhiteCurve(_HullWhiteFactor):

    def __call__(self, x, y=None):
        if y is not None:
            return self(y) / self(x)
        t = self.t
        x += t  # todo: verify spot shift to t
        df = continuous_compounding(self.curve(x), x)
        df /= continuous_compounding(self.curve(t), t)
        b = self.model.calc_integral_b(t, x)
        a = exp(-0.5 * b ** 2 * self.model.calc_integral_two(0.0, t))
        return continuous_rate(df * a * exp(-b * self.get(t, 0.)), x)


class _HullWhiteFx(_HullWhiteFactor):

    def __float__(self):
        t = self.t
        return self.curve(t) * exp(self.get(t, 0.))

    def evolve(self, step_size=.25, q=None):
        t = self.t
        x = t + step_size
        self[x] = self.model.evolve_fx(t, x, self.get(t, 0.), q)


@pretty
class _HullWhiteGlobal:
    random = Random()

    @staticmethod
    def build_correlation(rate_correlation=(), fx_correlation=(),
                          rate_fx_correlation=()):
        """builds big correlation matrix with index
            dom, fx_1, foreign_1, fx_2, foreign_2, ...

        :param rate_correlation: dom, foreign_1, foreign_2, ... (symmetric)
        :param fx_correlation: fx_1, fx_2, ... (symmetric)
        :param rate_fx_correlation:
            dom, foreign_1, foreign_2, ... vs. fx_1, fx_2, ... (non symmetric)
        :return: dom, fx_1, foreign_1, fx_2, foreign_2, ... (symmetric)

        >>> from yieldcurves.models import HullWhite

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

        >>> corr = HullWhite.Global.build_correlation(rate_corr, fx_corr, rate_fx_corr)
        >>> corr
        [[1.0, 0.11, 0.6, 0.12, 0.8],
         [0.11, 1.0, 0.21, 0.3, 0.31],
         [0.6, 0.21, 1.0, 0.22, 0.7],
         [0.12, 0.3, 0.22, 1.0, 0.32],
         [0.8, 0.31, 0.7, 0.32, 1.0]]

        """
        # init correlation matrix
        #  dom, foreign_1, foreign_2, ..., fx_1, fx_2, ...
        dim = len(rate_correlation)
        correlation = Identity(dim + dim - 1)
        correlation[:dim, :dim] = Matrix(rate_correlation)
        correlation[1 - dim:, 1 - dim:] = Matrix(fx_correlation)
        correlation[:dim, 1 - dim:] = Matrix(rate_fx_correlation)
        correlation[1 - dim:, :dim] = Matrix(rate_fx_correlation).T

        # sort index
        #  dom, fx_1, foreign_1, fx_2, foreign_2, ...
        permutation = Identity(dim + dim - 1)
        s = [i * 2 for i in range(dim)] + [j * 2 + 1 for j in range(dim - 1)]
        permutation[:, :] = permutation[:, s]

        return (permutation @ correlation @ permutation.T).tolist()

    @staticmethod
    def build_factors(curves, fx=None, *,
                      mean_reversion=(), volatility=(), terminal_date=1.,
                      domestic=None, fx_volatility=()):
        """builds list of HullWhite factors (curve + optional fx)

        :param curves: list of yield curves
        :param fx: list of fx rates (optional: default not -> no fx factors)
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

        >>> from yieldcurves.models import HullWhite

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
        [HullWhite.Fx(1.2, model=HullWhite(0.12, 0.06, domestic=HullWhite(0.1, 0.04))),
         HullWhite.Curve(0.02, model=HullWhite(0.12, 0.06, domestic=HullWhite(0.1, 0.04))),
         HullWhite.Fx(2.3, model=HullWhite(0.21, 0.07, domestic=HullWhite(0.1, 0.04))),
         HullWhite.Curve(0.03, model=HullWhite(0.21, 0.07, domestic=HullWhite(0.1, 0.04)))]

        """
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
            if fx is not None:
                # add fx if given
                factors.append(model.fx(fx.get(i, 1.)))
            factors.append(model.curve(c))
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
        factors = cls.build_factors(curves,
                                    fx=fx,
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

        >>> HullWhite.Global([domestic] + factors, correlation=corr)

        or

        >>> g = HullWhite.Global([domestic] + factors)
        >>> g.correlation = corr

        >>> print(*(f(.5)) for f in g.factors))

        >>> g.evolve()
        >>> print(*(dict(f.items()) for f in g.factors))
        >>> print(*(f(.5)) for f in g.factors))

        >>> g.evolve()
        >>> print(*(dict(f.items()) for f in g.factors))
        >>> print(*(f(.5)) for f in g.factors))

        >>> g.clear()
        >>> print(*(f(.5)) for f in g.factors))

        """
        # set first factor as domestic
        domestic, *factors = factors

        # validate domestic
        if domestic.model.domestic is not None:
            msg = f"domestic model must not have domestic model {domestic}"
            raise ValueError(msg)

        # validate model order
        for i in range(0, len(factors), 2):
            if not isinstance(factors[i + 1], _HullWhiteCurve):
                cls = factors[i].__class__.__qualname__
                raise ValueError(f'curve factor {i + 1} of wrong type: {cls}')
            if not isinstance(factors[i], _HullWhiteFx):
                cls = factors[i].__class__.__qualname__
                raise ValueError(f'fx factor {i} of wrong type: {cls}')
            if not factors[i].model == factors[i + 1].model:
                raise ValueError(f'factor model {i}  and {i + 1} differ')
            if not factors[i].model.domestic == domestic.model:
                d = factors[i].model.domestic
                msg = f"domestic factor model {str(d)!r}" \
                      f" differs from {str(domestic.model)!r}"
                raise ValueError(msg)

        self.factors = (domestic,) + tuple(factors)
        self.correlation = correlation

        if correlation is not None and \
                not len(self.factors) == len(correlation):
            msg = f"correlation of wrong size {len(correlation)}" \
                  f" expected size {len(factors)}"
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
        return self.factors[0]

    @property
    def t(self):
        return self.domestic.t

    def evolve(self, step_size=.25):
        if not self.factors:
            return
        random = self.factors[0].model.random
        c = self.cholesky(str(self.correlation))  # hack to use @cache
        q = [random.gauss(0., 1.) for _ in range(len(self.factors))]
        q = c.dot(q) if c is not None else q
        for i, f in enumerate(self.factors):
            if isinstance(f, _HullWhiteCurve):
                f.evolve(step_size, q[i])
            elif isinstance(f, _HullWhiteFx):
                f.evolve(step_size, [q[0], q[i], q[i + 1]])
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

    class Curve(_HullWhiteCurve): ...

    class Fx(_HullWhiteFx): ...

    class Global(_HullWhiteGlobal): ...


if __name__ == '__main__':

    rates = 'EUR', 'USD', 'GBP'
    fx = 'EURUSD', 'EURGBP'

    rate_corr = [
        [1.0, 0.6, 0.8],
        [0.6, 1.0, 0.7],
        [0.8, 0.7, 1.0]
    ]
    fx_corr = [
        [1.0, 0.3],
        [0.3, 1.0]
    ]
    rate_fx_corr = [
        [0.01, 0.20],
        [0.11, 0.12],
        [0.12, 0.21]
    ]

    corr = HullWhite.Global.merge_correlation(rate_corr, fx_corr, rate_fx_corr)
    print(corr)
