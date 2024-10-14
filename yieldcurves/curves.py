# -*- coding: utf-8 -*-

# yieldcurves
# -----------
# A Python library for financial yield curves.
#
# Author:   sonntagsgesicht
# Version:  0.2.5, copyright Monday, 14 October 2024
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


from warnings import warn

try:
    from curves import init, Curve  # noqa E401 E402
    from curves.numerics import (integrate,  # noqa E401 E402
                                 bisection_method,  # noqa E401 E402
                                 newton_raphson,  # noqa E401 E402
                                 secant_method)  # noqa E401 E402
except ImportError as e:  # noqa F941
    init = Curve = bisection_method = newton_raphson = secant_method = \
        integrate = warn(str(e))  # noqa F821
