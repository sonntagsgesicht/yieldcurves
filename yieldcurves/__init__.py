# -*- coding: utf-8 -*-

# yieldcurves
# -----------
# A Python library for financial yield curves.
#
# Author:   sonntagsgesicht
# Version:  0.2.2, copyright Thursday, 22 August 2024
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


__doc__ = 'A Python library for financial yield curves.'
__version__ = '0.2.2'
__dev_status__ = '4 - Beta'
__date__ = 'Thursday, 26 September 2024'
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

# todo:
#  [ ] extract .tools to extra projects
#  [ ] consolidate .tools.fit, .tools.numerics and .interpolation.fit
#  [ ] add global calibration using 'lmfit' (https://lmfit.github.io/lmfit-py/)


from . import compounding  # noqa E401 E402
from . import interpolation  # noqa E401 E402

from .datecurves import DateCurve  # noqa E401 E402
from .tools.algebra import AlgebraCurve  # noqa E401 E402
from .tools.mpl import plotter  # noqa E401 E402
from .tools.pp import pretty  # noqa E401 E402
from .tools.eye import eye  # noqa E401 E402
from .tools.constant import constant, init  # noqa E401 E402
from .yieldcurves import *  # noqa E401 E402
