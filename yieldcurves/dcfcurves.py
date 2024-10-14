# -*- coding: utf-8 -*-

# yieldcurves
# -----------
# A Python library for financial yield curves.
#
# Author:   sonntagsgesicht
# Version:  0.2.6.1, copyright Monday, 14 October 2024
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


from .tools import prettyclass
from .datecurves import DateCurve


@prettyclass
class DcfCurve(DateCurve):

    def get_discount_factor(self, start, stop=None):
        return self.curve.df(start, stop)

    def get_zero_rate(self, start, stop=None):
        return self.curve.zero(start, stop)

    def get_short_rate(self, start):
        return self.curve.short(start)

    def get_cash_rate(self, start, stop=None, step=None):
        stop = start + step if stop is None else stop
        return self.curve.cash(start, stop)

    def get_swap_annuity(self, date_list):
        return self.curve.annuity(date_list)

    def get_survival_prob(self, start, stop=None):
        return self.curve.prob(start, stop)

    def get_flat_intensity(self, start, stop=None):
        return self.curve.intensity(start, stop)

    def get_hazard_rate(self, start):
        return self.curve.hz(start)
