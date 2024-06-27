from datetime import datetime
from math import exp

import requests
from vectorizeit import vectorize

from .tools.pp import pretty

"""_params = {
    'beta0': 1.0138959988,
    'beta1': 1.836312606,
    'beta2': 2.9874138836,
    'beta3': 4.8105550065,
    'tau1': 0.7389058665,
    'tau2': 12.0362372437,
}"""


@vectorize(keys='x')
def spot_rate(x, *,
              beta0=0.0, beta1=0.0, beta2=0.0, beta3=0.0,
              tau1=1.0, tau2=1.0):
    x = float(x) or 1e-8
    a = (1 - exp(-x / tau1)) / (x / tau1)
    b = a - exp(-x / tau1)
    c = (1 - exp(-x / tau2)) / (x / tau2) - exp(-x / tau2)
    beta = beta0, beta1, beta2, beta3
    return 0.01 * sum(b * c for b, c in zip(beta, (1, a, b, c)))


@vectorize(keys='x')
def short_rate(x, *,
               beta0=0.0, beta1=0.0, beta2=0.0, beta3=0.0,
               tau1=1.0, tau2=1.0):
    x = float(x) or 1e-8
    a = exp(-x / tau1)
    b = a * x / tau1
    c = exp(-x / tau2) * x / tau2
    beta = beta0, beta1, beta2, beta3
    return 0.01 * sum(b * c for b, c in zip(beta, (1, a, b, c)))


def download_ecb(start='', end='', last=None, aaa_only=True):
    root = "https://data-api.ecb.europa.eu/service/data/YC/"
    aaa = "B.U2.EUR.4F.G_N_A.SV_C_YM"
    all = "B.U2.EUR.4F.G_N_C.SV_C_YM"
    url = root + (aaa if aaa_only else all)

    keys = 'BETA0', 'BETA1', 'BETA2', 'BETA3', 'TAU1', 'TAU2',
    params = {"format": "csvdata"}
    if start:
        if isinstance(start, datetime):
            start = start.strftime('%Y-%m-%d')
        params["startPeriod"] = start
    if end:
        if isinstance(end, datetime):
            end = end.strftime('%Y-%m-%d')
        params["endPeriod"] = end
    if last or len(params) == 1:
        params["lastNObservations"] = last or 1

    pos = slice(7, 10)

    res = {}
    for key in keys:
        response = requests.get(url + '.' + key, params=params, timeout=15)
        if not response.status_code == 200:
            response.raise_for_status()
        for line in response.text.split('\n')[1:]:
            if line:
                key, date, value = line.split(',')[pos]
                res[date] = res.get(date, {})
                res[date][key.lower()] = float(value)
    return res


@pretty
class NelsonSiegelSvensson:
    __slots__ = 'beta0', 'beta1', 'beta2', 'beta3', 'tau1', 'tau2'

    _download = {}

    def __init__(self, *,
                 beta0=0.0, beta1=0.0, beta2=0.0, beta3=0.0,
                 tau1=1.0, tau2=1.0):
        self.beta0 = beta0
        self.beta1 = beta1
        self.beta2 = beta2
        self.beta3 = beta3
        self.tau1 = tau1
        self.tau2 = tau2

    def __call__(self, x):
        params = {k: getattr(self, k) for k in self.__slots__}
        return spot_rate(x, **params)

    @classmethod
    def download(cls, date=None):
        if not cls._download:
            cls._download = download_ecb()
        if date is None:
            *_, date = tuple(cls._download)
        if isinstance(date, datetime):
            date = date.strftime('%Y-%m-%d')
        if date not in cls._download:
            cls._download.update(download_ecb(start=date, end=date))
            cls._download = dict(sorted(cls._download.items()))
        return cls(**cls._download[date])

    @classmethod
    @property
    def download_dates(cls):
        return tuple(cls._download)


class NelsonSiegelSvenssonShortRate(NelsonSiegelSvensson):

    def __call__(self, x):
        params = {k: getattr(self, k) for k in self.__slots__}
        return short_rate(x, **params)
