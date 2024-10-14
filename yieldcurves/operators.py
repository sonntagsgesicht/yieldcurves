# -*- coding: utf-8 -*-

# yieldcurves
# -----------
# A Python library for financial yield curves.
#
# Author:   sonntagsgesicht
# Version:  0.2.6.1, copyright Monday, 14 October 2024
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


from .yieldcurves import YieldCurve
from .tools import snake_case


class YieldCurveOperator:

    def __init__(self, curve: YieldCurve):
        r"""Operator turning |YieldCurve| into simple callable

        >>> from yieldcurves import YieldCurve
        >>> from yieldcurves.interpolation import linear
        >>> yc = YieldCurve(linear([0, 10], [0.01, 0.02]), spot_price=10)

        Turn yield curve into general finanical curve like ...

        ... a price curve

        >>> from yieldcurves import Price
        >>> p = Price(yc)

        >>> p(1.234)
        10.139592895598932

        >>> yc.price(1.234) == p(1.234)
        True

        ... a spot rate curve

        >>> from yieldcurves import Spot
        >>> s = Spot(yc)

        >>> s(1.234)
        0.011233999999999886

        >>> yc.spot(1.234) == s(1.234)
        True

        ... a short rate curve

        >>> from yieldcurves import Short
        >>> sh = Short(yc)

        >>> sh(1.234)
        0.012468004483236131

        >>> yc.short(1.234) == sh(1.234)
        True

        ... or into interest rate related curve like ...

        ... a discount factor curve

        >>> from yieldcurves import Df
        >>> df = Df(yc)

        >>> df(1.234)
        0.9862328895216768

        >>> yc.df(1.234) == df(1.234)
        True

        ... a zero rate curve

        >>> from yieldcurves import Zero
        >>> z = Zero(yc)

        >>> z(1.234)
        0.011233999999999886

        >>> yc.zero(1.234) == z(1.234)
        True

        ... a cash rate curve

        >>> from yieldcurves import Cash
        >>> ch = Cash(yc)

        >>> ch(1.234)
        0.012738239885720759

        >>> yc.cash(1.234) == ch(1.234)
        True

        ... a swap annuity curve

        >>> from yieldcurves import Annuity
        >>> an = Annuity(yc)

        >>> an(1.234)
        1.2198387749234412

        >>> yc.annuity(1.234) == an(1.234)
        True

        ... a swap par rate curve

        >>> from yieldcurves import Swap
        >>> sw = Swap(yc)

        >>> sw(1.234)
        0.01128600825071107

        >>> yc.swap(1.234) == sw(1.234)
        True

        ... or into credit related curve like ...

        ... a survival probability curve

        >>> from yieldcurves import Prob
        >>> pb = Prob(yc)

        >>> pb(1.234)
        0.9862328895216768

        >>> yc.prob(1.234) == pb(1.234)
        True

        ... a intensity curve

        >>> from yieldcurves import Intensity
        >>> it = Intensity(yc)

        >>> it(1.234)
        0.011233999999999886

        >>> yc.intensity(1.234) == it(1.234)
        True

        ... a hazard rate curve

        >>> from yieldcurves import Hz
        >>> hz = Hz(yc)

        >>> hz(1.234)
        0.012468004483236131

        >>> yc.hz(1.234) == hz(1.234)
        True

        ... a probalility of default curve

        >>> from yieldcurves import Pd
        >>> pd = Pd(yc)

        >>> pd(1.234)
        0.013767110478323241

        >>> yc.pd(1.234) == pd(1.234)
        True

        ... a marginal/annual survival probalility curve

        >>> from yieldcurves import Marginal
        >>> mg = Marginal(yc)

        >>> mg(1.234)
        0.9866222877257945

        >>> yc.marginal(1.234) == mg(1.234)
        True

        ... a marginal/annual probalility of default curve

        >>> from yieldcurves import MarginalPd
        >>> md = MarginalPd(yc)

        >>> md(1.234)
        0.013377712274205478

        >>> yc.marginal_pd(1.234) == md(1.234)
        True

        """
        self.curve = (
            curve) if isinstance(curve, YieldCurve) else YieldCurve(curve)

    def __call__(self, x, y=None):
        name = snake_case(self.__class__.__name__)
        if hasattr(self.curve, name):
            if y is None:
                return getattr(self.curve, name)(x)
            return getattr(self.curve, name)(x, y)
        msg = f"curve attribute of type {self.__class__.__name__!r} " \
              f"object has no attribute {name!r} that can be called"
        raise AttributeError(msg)

    def __str__(self):
        return f"{self.__class__.__qualname__}({self.curve!s})"

    def __repr__(self):
        return f"{self.__class__.__qualname__}({self.curve!r})"


class Price(YieldCurveOperator):
    """price curve from |YieldCurve| (for docs see |YieldCurveOperator|)"""
    pass


class Spot(YieldCurveOperator):
    """spot rate curve from |YieldCurve|"""
    pass


class Short(YieldCurveOperator):
    """spot rate curve from |YieldCurve|"""
    pass


# --- interest rate operators ---

class Df(YieldCurveOperator):
    """discount factor curve from |YieldCurve|"""
    pass


class Zero(YieldCurveOperator):
    """zero coupon bond rate curve from |YieldCurve|"""
    pass


class Cash(YieldCurveOperator):
    """cash rate curve from |YieldCurve|"""
    pass


class Annuity(YieldCurveOperator):
    """swap annuity curve from |YieldCurve|"""
    pass


class Swap(YieldCurveOperator):
    """swap par rate curve from |YieldCurve|"""
    pass


# --- credit prob operators ---


class Prob(YieldCurveOperator):
    """survival probability curve from |YieldCurve|"""
    pass


class Intensity(YieldCurveOperator):
    """intensity curve from |YieldCurve|"""
    pass


class Hz(YieldCurveOperator):
    """hazard rate curve from |YieldCurve|"""
    pass


class Pd(YieldCurveOperator):
    """probability of default curve from |YieldCurve|"""
    pass


class Marginal(YieldCurveOperator):
    """annual survival probability curve from |YieldCurve|"""
    pass


class MarginalPd(YieldCurveOperator):
    """annual probability of default curve from |YieldCurve|"""
    pass
