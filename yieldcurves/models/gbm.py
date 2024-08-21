# -*- coding: utf-8 -*-

# yieldcurves
# -----------
# A Python library for financial yield curves.
#
# Author:   sonntagsgesicht
# Version:  0.2.1, copyright Wednesday, 21 August 2024
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


from functools import cache
from math import exp
from random import Random

from ..tools import integrate
from ..yieldcurves import init


class GBM(dict):
    random = Random()  # nosec B311

    def __init__(self, curve, *, volatility=0.0):
        """

        :param float curve: fx rate
        :param float: volatility
            (optional) Default: either inner_factor.volatility or 0.0
        :param float: step size

        """
        super().__init__()
        self.curve = init(curve)
        self.volatility = init(volatility)
        # todo: volatility = init(getattr(curve, 'volatility', volatility))

    def __float__(self):
        # current state / last entry
        return next(reversed(self)) if self else 0.0

    # integrate drift and diffusion integrals

    @cache
    def calc_diffusion_integrals(self, s, e):
        return integrate(self.volatility, s, e)

    # risk factor methods

    def _evolve(self, t1, t2, x=0., q=None):
        v = self.calc_diffusion_integrals(t1, t2)
        if q is None:
            q = self.random.gauss(0., 1.)
        return x * exp(v * q)

    def evolve(self, step_size=0.25, q=None):
        t = float(self)
        x = t + step_size
        return self._evolve(t, x, self.get(t, 1.), q)

    # curve methods

    def __call__(self, x, y=None):
        if y is not None:
            msg = f"y argument must not be set in {self.__class__.__name__}"
            raise TypeError(msg)
        t = float(self)
        x += t
        return self.get(t, 1.) * self.curve(x)
