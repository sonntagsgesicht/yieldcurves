from math import exp
from random import Random

from scipy import integrate

from ..yieldcurves import _const


class GBM:

    def __init__(self, curve, *, volatility=0.0, step_size=0.25):
        """

        :param float curve: fx rate
        :param float: volatility
            (optional) Default: either inner_factor.volatility or 0.0
        :param float: step size

        """
        if not isinstance(curve, float) and not callable(curve):
            msg = f"{self.__class__.__name__} requires curve " \
                  f"of type {float.__name__}" \
                  f"but {curve.__class__.__name__} is given"
            raise TypeError(msg)

        self.curve = curve if callable(curve) else _const(curve)

        # todo:
        #   self.volatility = getattr(curve, 'volatility', _const(volatility))
        self.volatility = \
            volatility if callable(volatility) else _const(volatility)

        # init random
        self.random = Random()
        self.state = {0.0: 1.0}
        self.step_size = step_size

        self._pre_calc_drift = dict()
        self._pre_calc_diffusion = dict()

    # integrate drift and diffusion integrals

    def _calc_drift_integrals(self, s, e):

        if (s, e) in self._pre_calc_drift:
            return self._pre_calc_drift[s, e]

        # todo: GBMFx._calc_drift_integrals
        part, *_ = integrate.quad(self.volatility, s, e)
        self._pre_calc_drift[s, e] = part
        return part

    def _calc_diffusion_integrals(self, s, e):

        if (s, e) in self._pre_calc_diffusion:
            return self._pre_calc_diffusion[s, e]

        # todo: GBMFx._calc_diffusion_integrals
        part, *_ = integrate.quad(self.volatility, s, e)
        self._pre_calc_diffusion[s, e] = part
        return part

    # risk factor methods

    def evolve(self, step_size=None, q=None):
        step_size = step_size or self.step_size
        s = next(reversed(self.state))  # current state / last entry
        e = s + step_size
        d = self._calc_drift_integrals(s, e)
        v = self._calc_diffusion_integrals(s, e)

        if q is None:
            q = self.random.gauss(0., 1.)

        x = self.state[s]
        y = self.state[e] = x * exp(d + v * q)
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
        s = next(reversed(self.state))  # current state / last entry
        return self.state[s]
