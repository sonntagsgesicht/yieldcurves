# -*- coding: utf-8 -*-

# yieldcurves
# -----------
# A Python library for financial yield curves.
#
# Author:   sonntagsgesicht
# Version:  0.2.1, copyright Wednesday, 21 August 2024
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


from math import sqrt
from random import Random

from scipy.linalg import cholesky


class Gauss:
    random = Random()  # nosec B311

    def __init__(self, covariance=None, term=1.0, increments=10, seed=None):
        self.covariance = covariance
        self._cholesky = cholesky(self.covariance)

        self.state = 0.0
        self._states = {self.state: [0.0] * len(covariance)}

    def __call__(self):
        c = self._cholesky
        q = [self.random.gauss(0., 1.) for _ in range(len(c))]
        return list(c.dot(q))

    def __len__(self):
        return len(self._states)

    def __getattr__(self, item):
        return self._states.get(item, self.evolve(item))

    def __iter__(self):
        return iter(self._states.values())

    def evolve(self, increment=None):
        return

    def reset(self, y=0.0):
        self._states = {x: s for x, s in self._states if x <= y}

    def sample(self, increments=10):
        return


class StochasticProcess:

    def __init__(self, step_size=0.25, driver=None):
        """
            base class for stochastic process :math:`X`,
            e.g. Wiener process :math:`W` or Markov chain :math:`M`

        """
        self.driver = driver or Random()  # nosec B311

        self.step_size = step_size
        self.state = {0.0: 0.0}

    def _evolve(self, x, s, e, q):
        """ evolves process state `x` from `s` to `e`

        in time depending on standard normal random variable `q`

        :param float x: current state value,
            i.e. value before evolution step
        :param float s: current point in time,
            i.e. start point of next evolution step
        :param float e: next point in time,
            i.e. end point of evolution step
        :param float q: standard normal random number to do step

        :return: next state value, i.e. value after evolution step
        :rtype: float

        """
        return q

    def evolve(self, step_size=None):
        step_size = step_size or self.step_size
        s = next(reversed(self.state))  # current state / last entry
        e = s + step_size
        q = self.driver.gauss(0., 1.)
        x = self.state[s]
        y = self.state[e] = self._evolve(x, s, e, q)
        return y


class ItoProcess(StochasticProcess):

    def _drift(self, x, s, e):
        return 0.0

    def _diffusion(self, x, s, e):
        return sqrt(e - s)

    def _evolve(self, x, s, e, q):
        """ evolves process state `x` from `s` to `e`

        in time depending on standard normal random variable `q`

        :param float x: current state value,
            i.e. value before evolution step
        :param float s: current point in time,
            i.e. start point of next evolution step
        :param float e: next point in time,
            i.e. end point of evolution step
        :param float q: standard normal random number to do step

        :return: next state value, i.e. value after evolution step
        :rtype: float

        """
        return x + self._drift(x, s, e) + self._diffusion(x, s, e) * q
