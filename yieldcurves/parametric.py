from math import exp

from .repr import representation


class NelsonSiegelSvensson:

    def __init__(self, beta_0=0.0, beta_1=0.0, beta_2=0.0, beta_3=0.0,
                 tau_0=1.0, tau_1=1.0):
        self.beta = beta_0, beta_1, beta_2, beta_3
        self.tau = tau_0, tau_1

    def __repr__(self):
        return representation(self, *self.beta, *self.tau)

    def __call__(self, x):
        return self.zero(x)

    def zero(self, x):
        tau_zero, tau_one = self.tau
        a = (1 - exp(-x / tau_zero)) / (x / tau_zero)
        b = a - exp(-x / tau_zero)
        c = (1 - exp(-x / tau_one)) / (x / tau_one) - exp(-x / tau_one)
        return sum(b * c for b, c in zip(self.beta, (1, a, b, c)))

    def short(self, x):
        tau_zero, tau_one = self.tau
        a = exp(-x / tau_zero)
        b = a * x / tau_zero
        c = exp(-x / tau_one) * x / tau_one
        return sum(b * c for b, c in zip(self.beta, (1, a, b, c)))


class SABR:

    def __init__(self, alpha, beta, gamma, rho):
        self.sabr = alpha, beta, gamma, rho
        self.atm = None

    def __repr__(self):
        return representation(self, *self.sabr)

    def vol(self, x):
        # todo implement sabr formula
        alpha, beta, gamma, rho = self.sabr
        if self.atm is not None:
            alpha = self.atm
        return x
