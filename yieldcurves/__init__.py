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
__version__ = '0.2.4'
__dev_status__ = '4 - Beta'
__date__ = 'Sunday, 13 October 2024'
__author__ = 'sonntagsgesicht'
__email__ = 'sonntagsgesicht@icloud.com'
__url__ = 'https://github.com/sonntagsgesicht/' + __name__
__license__ = 'Apache License 2.0'
__dependencies__ = 'vectorizeit', 'prettyclass', 'curves'
__dependency_links__ = ()
__data__ = ()
__scripts__ = ()
__theme__ = 'sphinx_rtd_theme'

import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

# todo:
#  [ ] add tutorial incl. curve fitting
#  [ ] add global calibration using 'lmfit' (https://lmfit.github.io/lmfit-py/)


from . import compounding  # noqa E401 E402
from . import interpolation  # noqa E401 E402

from .datecurves import DateCurve  # noqa E401 E402
from .operators import *  # noqa E401 E402
from .yieldcurves import YieldCurve  # noqa E401 E402
