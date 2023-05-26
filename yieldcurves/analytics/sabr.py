
from ..repr import representation


class sabr:

    def __init__(self, alpha, beta, gamma, rho):
        self.sabr = alpha, beta, gamma, rho
        self.atm = None

    def __repr__(self):
        keys = 'alpha', 'beta', 'gamma', 'rho'
        vals = self.sabr
        return representation(self, **dict(zip(keys, vals)))

    def vol(self, x):
        # todo implement sabr formula
        alpha, beta, gamma, rho = self.sabr
        if self.atm is not None:
            alpha = self.atm
        return x
