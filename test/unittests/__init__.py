# -*- coding: utf-8 -*-

# yieldcurves
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.4, copyright Saturday, 10 October 2020
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


import sys
sys.path.append('yieldcurves/')
sys.path.append('.')
sys.path.append('..')

# from .curve_tests import *
from .creditcurve_tests import *
from .compounding_tests import *
from .interestratecurve_tests import *
from .interpolation_tests import *
from .fx_tests import *
from .forwardcurve_tests import *
