from math import exp

from ..repr import representation


class nelson_siegel_svensson:

    def __init__(self, beta0=0.0, beta1=0.0, beta2=0.0, beta3=0.0,
                 tau0=1.0, tau1=1.0):
        self.beta = beta0, beta1, beta2, beta3
        self.tau = tau0, tau1

    def __repr__(self):
        return representation(self, *self.beta, *self.tau)

    def __call__(self, x):
        return self.zero(x)

    def zero(self, x):
        tau0, tau1 = self.tau
        a = (1 - exp(-x / tau0)) / (x / tau0)
        b = a - exp(-x / tau0)
        c = (1 - exp(-x / tau1)) / (x / tau1) - exp(-x / tau1)
        return sum(b * c for b, c in zip(self.beta, (1, a, b, c)))

    def short(self, x):
        tau0, tau1 = self.tau
        a = exp(-x / tau0)
        b = a * x / tau0
        c = exp(-x / tau1) * x / tau1
        return sum(b * c for b, c in zip(self.beta, (1, a, b, c)))
