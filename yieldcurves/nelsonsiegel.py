# -*- coding: utf-8 -*-

# yieldcurves
# -----------
# A Python library for financial yield curves.
#
# Author:   sonntagsgesicht
# Version:  0.2.6.1, copyright Monday, 14 October 2024
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


from datetime import date
from math import exp

import requests

from .tools import vectorize
from .tools import prettyclass


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
    r"""Nelson Siegel Svensson spot interest rate term structure

    :param x: maturity
    :param beta0: $\beta_0$ parameter
    :param beta1: $\beta_1$ parameter
    :param beta2: $\beta_2$ parameter
    :param beta3: $\beta_3$ parameter
    :param tau1: $\tau_1$ decay parameter
    :param tau2: $\tau_2$ decay parameter
    :return: spot rate $R(x)$ at **x**

    .. math::

        R(x) = \beta_0
             + \beta_1 \left( \frac{1 - e^{-\frac{x}{\tau_1}}}{\frac{x}{\tau_1}} \right)
             + \beta_2 \left( \frac{1 - e^{-\frac{x}{\tau_1}}}{\frac{x}{\tau_1}} - e^{-\frac{x}{\tau_1}} \right)
             + \beta_3 \left( \frac{1 - e^{-\frac{x}{\tau_2}}}{\frac{x}{\tau_2}} - e^{-\frac{x}{\tau_2}} \right)

    """  # noqa 501
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
    r"""Nelson Siegel Svensson interest short rate (instantaneous spot rate)

    :param x: maturity
    :param beta0: $\beta_0$ parameter
    :param beta1: $\beta_1$ parameter
    :param beta2: $\beta_2$ parameter
    :param beta3: $\beta_3$ parameter
    :param tau1: $\tau_1$ decay parameter
    :param tau2: $\tau_2$ decay parameter
    :return: short rate at $r(x)$ **x**

    .. math::

        r(x) = \beta_0
             + \beta_1 \left( e^{-\frac{x}{\tau_1}} \right)
             + \beta_2 \left( e^{-\frac{x}{\tau_1}} \frac{x}{\tau_1} \right)
             + \beta_3 \left( e^{-\frac{x}{\tau_2}} \frac{x}{\tau_2} \right)

    """
    x = float(x) or 1e-8
    a = exp(-x / tau1)
    b = a * x / tau1
    c = exp(-x / tau2) * x / tau2
    beta = beta0, beta1, beta2, beta3
    return 0.01 * sum(b * c for b, c in zip(beta, (1, a, b, c)))


def download_ecb(start='', end='', last=None, aaa_only=True):
    """download term structure parameters from ecb (European Central Bank)

    :param str or date start: start date of download period (optional)
    :param str or date end: end date of download period (optional)
    :param int last: number of observations (optional)
    :param bool aaa_only: flag to decide whether load parameters
        estimated from **AAA** rated only euro government bonds
        or all euro government bonds
    :return: dict[str, dict[str, float]] dictionary
        with keys 'YYYY-MM-DD' and values parameter dict

    If no arguments to select dates are given latest parameters are loaded.

    >>> from yieldcurves.nelsonsiegel import spot_rate, download_ecb

    """
    root = "https://data-api.ecb.europa.eu/service/data/YC/"
    aaa = "B.U2.EUR.4F.G_N_A.SV_C_YM"
    all = "B.U2.EUR.4F.G_N_C.SV_C_YM"
    url = root + (aaa if aaa_only else all)

    keys = 'BETA0', 'BETA1', 'BETA2', 'BETA3', 'TAU1', 'TAU2',
    params = {"format": "csvdata"}
    if start:
        if isinstance(start, date):
            start = start.strftime('%Y-%m-%d')
        params["startPeriod"] = start
    if end:
        if isinstance(end, date):
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
                key, _date, value = line.split(',')[pos]
                res[_date] = res.get(_date, {})
                res[_date]['timestamp'] = _date
                res[_date][key.lower()] = float(value)
    return res


@prettyclass(init=False)
class NelsonSiegelSvensson:
    downloads = {}
    """dictionary of downloaded curves with keys as dates as string"""

    def __init__(self, *,
                 beta0=0.0, beta1=0.0, beta2=0.0, beta3=0.0,
                 tau1=1.0, tau2=1.0, timestamp=None):
        r"""Nelson Siegel Svensson interest term structure cruve

        :param beta0: $\beta_0$ parameter
        :param beta1: $\beta_1$ parameter
        :param beta2: $\beta_2$ parameter
        :param beta3: $\beta_3$ parameter
        :param tau1: $\tau_1$ decay parameter
        :param tau2: $\tau_2$ decay parameter
        :param timestamp: timestamp of curve

        >>> from yieldcurves import NelsonSiegelSvensson

        """
        self.beta0 = beta0
        self.beta1 = beta1
        self.beta2 = beta2
        self.beta3 = beta3
        self.tau1 = tau1
        self.tau2 = tau2
        self.timestamp = timestamp

    def __call__(self, x):
        return self.spot(x)

    @property
    def __ts__(self):
        return date.fromisoformat(self.timestamp)

    def spot(self, x):
        r"""spot interest rate

        :param x: maturity
        :return: spot rate $R(x)$ at **x**

        .. math::

            R(x) = \beta_0
                 + \beta_1 \left( \frac{1 - e^{-\frac{x}{\tau_1}}}{\frac{x}{\tau_1}} \right)
                 + \beta_2 \left( \frac{1 - e^{-\frac{x}{\tau_1}}}{\frac{x}{\tau_1}} - e^{-\frac{x}{\tau_1}} \right)
                 + \beta_3 \left( \frac{1 - e^{-\frac{x}{\tau_2}}}{\frac{x}{\tau_2}} - e^{-\frac{x}{\tau_2}} \right)

        """  # noqa 501
        return spot_rate(x,
                         beta0=self.beta0, beta1=self.beta1, beta2=self.beta2,
                         beta3=self.beta3, tau1=self.tau1, tau2=self.tau2)

    def short(self, x):
        r"""short rate (instantaneous spot rate)

        :param x: maturity
        :return: short rate $r(x)$ at **x**

        .. math::

            r(x) = \beta_0
                 + \beta_1 \left( e^{-\frac{x}{\tau_1}} \right)
                 + \beta_2 \left( e^{-\frac{x}{\tau_1}} \frac{x}{\tau_1} \right)
                 + \beta_3 \left( e^{-\frac{x}{\tau_2}} \frac{x}{\tau_2} \right)

        """  # noqa 501
        return short_rate(x,
                          beta0=self.beta0, beta1=self.beta1, beta2=self.beta2,
                          beta3=self.beta3, tau1=self.tau1, tau2=self.tau2)

    @classmethod
    def download(cls, t=None):
        """build curve with parameters from ecb
        :param t: date of parameters or (if of integer) latest parameter
        :return:

        >>> from yieldcurves import NelsonSiegelSvensson
        >>> nss = NelsonSiegelSvensson.download('2024-08-01')
        >>> nss
        NelsonSiegelSvensson(beta0=0.3930624673, beta1=3.0642695848, beta2=-6.0856376597, beta3=9.3989699383, tau1=4.0804649054, tau2=9.9328952349, timestamp='2024-08-01')

        or load a bulk of curves, here the last of the last 10 days

        >>> _ = NelsonSiegelSvensson.download(10)

        to get all already loaded curves

        >>> len(NelsonSiegelSvensson.downloads)
        11

        """  # noqa E501
        if isinstance(t, date):
            t = t.strftime('%Y-%m-%d')
        if t is None:
            # return latest available
            d = {k: cls(**v) for k, v in download_ecb().items()}
            cls.downloads.update(d)
            t = next(iter(d))  # pick first
        if isinstance(t, int):
            # load last t
            d = {k: cls(**v) for k, v in download_ecb(last=t).items()}
            cls.downloads.update(d)
            t = next(iter(d))  # pick first
        if t not in cls.downloads:
            # load missing t
            d = {k: cls(**v) for k, v in download_ecb(start=t, end=t).items()}
            cls.downloads.update(d)
        cls.downloads = dict(sorted(cls.downloads.items()))
        return cls.downloads[t]

    @classmethod
    @property
    def download_dates(cls):
        """available parameter dates"""
        return tuple(cls.downloads)


class NelsonSiegelSvenssonShortRate(NelsonSiegelSvensson):

    def __call__(self, x):
        return self.short(x)
