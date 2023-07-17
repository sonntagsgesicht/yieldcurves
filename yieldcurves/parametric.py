from math import exp
from collections import UserDict

from vectorizeit import vectorize


from .tools.repr import representation


class NelsonSiegelSvensson(UserDict):

    def __init__(self, beta0=0.0, beta1=0.0, beta2=0.0, beta3=0.0,
                 tau1=1.0, tau2=1.0):
        data = {
            'beta0': beta0,
            'beta1': beta1,
            'beta2': beta2,
            'beta3': beta3,
            'tau1': tau1,
            'tau2': tau2,
        }
        super().__init__(data)
        self.short_rate = False

    @vectorize()
    def __call__(self, x):
        x = float(x) or 1e-8
        if isinstance(x, (list, tuple)):
            return type(x)(self(_) for _ in x)
        *beta, tau1, tau2 = self.values()
        if self.short_rate:
            a = exp(-x / tau1)
            b = a * x / tau1
            c = exp(-x / tau2) * x / tau2
        else:
            a = (1 - exp(-x / tau1)) / (x / tau1)
            b = a - exp(-x / tau1)
            c = (1 - exp(-x / tau2)) / (x / tau2) - exp(-x / tau2)
        return 0.01 * sum(b * c for b, c in zip(beta, (1, a, b, c)))

    def __str__(self):
        return representation(self, **self.data, rstyle=False)

    def __repr__(self):
        return representation(self, **self.data, rstyle=True)

    def download(self):
        url = 'https://sdw-wsrest.ecb.europa.eu/' \
              'service/data/YC/B.U2.EUR.4F.G_N_A+G_N_C.SV_C_YM.?' \
              'lastNObservations=1&format=csvdata'  # noqa F841
        file = 'data.cvs'  # noqa F841
        # todo parse ecb parameter
        self.data = {
            'beta0': 1.0138959988,
            'beta1': 1.836312606,
            'beta2': 2.9874138836,
            'beta3': 4.8105550065,
            'tau1': 0.7389058665,
            'tau2': 12.0362372437,
        }
        return self
