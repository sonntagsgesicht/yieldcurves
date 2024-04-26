from collections import UserDict
from datetime import datetime
import io
from math import exp
import xml.etree.ElementTree as ET  # nosec B405

import requests
from vectorizeit import vectorize

from .tools.repr import representation


"""
_data = {
    'beta0': 1.0138959988,
    'beta1': 1.836312606,
    'beta2': 2.9874138836,
    'beta3': 4.8105550065,
    'tau1': 0.7389058665,
    'tau2': 12.0362372437,
}

# todo parse ecb parameter
url = 'https://sdw-wsrest.ecb.europa.eu/' \
      'service/data/YC/B.U2.EUR.4F.G_N_A+G_N_C.SV_C_YM.?' \
      'lastNObservations=1&format=csvdata'  # noqa F841
file = 'data.cvs'  # noqa F841
"""


@vectorize(keys='x')
def nss_spot(x,
             beta0=0.0, beta1=0.0, beta2=0.0, beta3=0.0, tau1=1.0, tau2=1.0):
    x = float(x) or 1e-8
    a = (1 - exp(-x / tau1)) / (x / tau1)
    b = a - exp(-x / tau1)
    c = (1 - exp(-x / tau2)) / (x / tau2) - exp(-x / tau2)
    beta = beta0, beta1, beta2, beta3
    return 0.01 * sum(b * c for b, c in zip(beta, (1, a, b, c)))


@vectorize(keys='x')
def nss_short(x,
             beta0=0.0, beta1=0.0, beta2=0.0, beta3=0.0, tau1=1.0, tau2=1.0):
    x = float(x) or 1e-8
    a = exp(-x / tau1)
    b = a * x / tau1
    c = exp(-x / tau2) * x / tau2
    beta = beta0, beta1, beta2, beta3
    return 0.01 * sum(b * c for b, c in zip(beta, (1, a, b, c)))


def nss_download():
    root = '{http://www.sdmx.org/' \
           'resources/sdmxml/schemas/v2_1/data/generic}'
    url = 'https://api.statistiken.bundesbank.de/rest/download/'
    keys = 'beta0', 'beta1', 'beta2', 'beta3', 'tau1', 'tau2',

    download = {}
    for x in keys:
        ref = f'D.I.ZST.{x[0] + x[-1]}.' \
              f'EUR.S1311.B.A604._Z.R.A.A._Z._Z.A'
        xml_file = requests.get(url + 'BBSIS/' + ref)
        tree = ET.parse(io.StringIO(xml_file.text))  # nosec B314

        for ob in tree.getroot().iter(root + 'Obs'):
            if ob.find(root + 'ObsValue') is not None:
                dt = ob.find(root + 'ObsDimension').attrib['value']
                obj = ob.find(root + 'ObsValue').attrib['value']
                values = download.get(dt, dict())
                values[x.lower()] = float(obj)
                download[dt] = values
    return download


class NelsonSiegelSvensson(UserDict):

    _download = dict()

    def __init__(self, beta0=0.0, beta1=0.0, beta2=0.0, beta3=0.0,
                 tau1=1.0, tau2=1.0):
        super().__init__(beta0=beta0, beta1=beta1, beta2=beta2, beta3=beta3,
                         tau1=tau1, tau2=tau2)
        self.short_rate = False
        self.date = None

    def __call__(self, x):
        return nss_short(x, **self) if self.short_rate else nss_spot(x, **self)

    def __str__(self):
        s = f" as of {self.date}" if self.date else ''
        return representation(self, **self.data, rstyle=False) + s

    def __repr__(self):
        if self.date:
            n = self.__class__.__qualname__
            return f"{n}.download({self.date})"
        return representation(self, **self.data, rstyle=False)

    @classmethod
    def download(cls, date=None):
        if not cls._download:
            cls._download = nss_download()

        if date:
            if isinstance(date, int):
                date = tuple(cls._download)[date]
            if isinstance(date, datetime):
                date = date.strftime('%Y-%m-%d')
            obj = cls(**cls._download[date])
            obj.date = date
            return obj
