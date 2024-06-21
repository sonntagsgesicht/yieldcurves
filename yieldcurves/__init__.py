# -*- coding: utf-8 -*-

# yieldcurves
# -----------
# A Python library for financial yield curves.
#
# Author:   sonntagsgesicht
# Version:  0.1, copyright Thursday, 12 April 2023
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


__doc__ = 'A Python library for financial yield curves.'
__version__ = '0.1'
__dev_status__ = '4 - Beta'
__date__ = 'Saturday, 22 April 2023'
__author__ = 'sonntagsgesicht'
__email__ = 'sonntagsgesicht@icloud.com'
__url__ = 'https://github.com/sonntagsgesicht/' + __name__
__license__ = 'Apache License 2.0'
__dependencies__ = ()
__dependency_links__ = ()
__data__ = ()
__scripts__ = ()
__theme__ = 'sphinx_rtd_theme'

import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

# todo:
#  add docs for new CurveAdapter
#  add sabr model
#  add global calibration using 'lmfit.minimize' or 'scipy.optimize.leastsq'

from . import compounding  # noqa E401 E402
from . import interpolation  # noqa E401 E402
from . import parametric  # noqa E401 E402

from .curves import *  # noqa E401 E402
