# -*- coding: utf-8 -*-

# yieldcurves
# -----------
# A Python library for financial yield curves.
#
# Author:   sonntagsgesicht
# Version:  0.2.2, copyright Thursday, 22 August 2024
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


from .pp import pretty


@pretty
class eye:
    def __init__(self, curve=None):
        r"""identity function $x \mapsto x$

        :param x: float
        :return: identity value **x**
        """
        self.curve = curve

    def __call__(self, x):
        return x if self.curve is None else self.curve(x)
