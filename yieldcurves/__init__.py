# -*- coding: utf-8 -*-

# yieldcurves
# -----------
# A Python library for financial yield curves.
#
# Author:   sonntagsgesicht
# Version:  0.2, copyright Monday, 01 July 2024
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


__doc__ = 'A Python library for financial yield curves.'
__version__ = '0.2'
__dev_status__ = '4 - Beta'
__date__ = 'Tuesday, 16 July 2024'
__author__ = 'sonntagsgesicht'
__email__ = 'sonntagsgesicht@icloud.com'
__url__ = 'https://github.com/sonntagsgesicht/' + __name__
__license__ = 'Apache License 2.0'
__dependencies__ = 'vectorizeit',
__dependency_links__ = ()
__data__ = ()
__scripts__ = ()
__theme__ = 'sphinx_rtd_theme'

import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

from . import compounding  # noqa E401 E402
from . import interpolation  # noqa E401 E402
from . import parametric  # noqa E401 E402

from .datecurves import DateCurve  # noqa E401 E402
from .yieldcurves import *  # noqa E401 E402
from .tools.pp import pretty  # noqa E401 E402


@pretty
class eye:
    r"""identity function $x \mapsto x$

    :param x: float
    :return: identity value **x**
    """
    def __init__(self, curve=None):
        self.curve = curve

    def __call__(self, x):
        return x if self.curve is None else self.curve(x)
