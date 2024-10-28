# -*- coding: utf-8 -*-

# yieldcurves
# -----------
# A Python library for financial yield curves.
#
# Author:   sonntagsgesicht
# Version:  0.2.7, copyright Monday, 14 October 2024
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


__doc__ = 'A Python library for financial yield curves.'
__version__ = '0.2.9'
__dev_status__ = '4 - Beta'
__date__ = 'Monday, 28 October 2024'
__author__ = 'sonntagsgesicht'
__email__ = 'sonntagsgesicht@icloud.com'
__url__ = 'https://github.com/sonntagsgesicht/' + __name__
__license__ = 'Apache License 2.0'
__dependencies__ = 'curves', 'prettyclass', 'vectorizeit'
__dependency_links__ = ()
__data__ = ()
__scripts__ = ()
__theme__ = 'sphinx_rtd_theme'

import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

# todo:
#  [ ] fixed dependencies !!!
#  [ ] add tutorial incl. curve fitting
#  [ ] rethink DateCurve, dyf and inverse
#  [ ] integrate currency.py
#  [ ] add pretty currency (111.23.. Mio EUR for 111_234_000 EUR)
#  [ ] add global calibration using 'lmfit' (https://lmfit.github.io/lmfit-py/)
#  [ ] _repr_html_ as plot  + details?
#  [x] make solver in fit optional w/- default (yc.nx)
#  [x] move interpolation to curve project
#  [ ] make YieldCurve and DateCurve algebraic
#  [x] add OptionPricingCurve
#  [ ] add VolatilityCurve
#  [ ] rethink yc.cash(x, y) as E[yc(y) | x], i.e. yc.cash(x, y) = yc.cash(y)?


from . import compounding, optionpricing  # noqa E401 E402

from .datecurves import DateCurve  # noqa E401 E402
from .hullwhite import HullWhite  # noqa E401 E402
from .nelsonsiegel import NelsonSiegelSvensson  # noqa E401 E402
from .operators import *  # noqa E401 E402
from .optioncurves import OptionPricingCurve  # noqa E401 E402
from .yieldcurves import YieldCurve  # noqa E401 E402
