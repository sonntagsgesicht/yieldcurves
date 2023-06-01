from math import prod

from .repr import attr, repr_attr, repr_algebra

from .daycount import day_count as _day_count
from .interpolation import linear
from . import interpolation as _interpolation


# --- base curve classes ---


class curve_wrapper:

    def __init__(self, curve, origin=None, call=None, invisible=False):
        self.curve = curve
        self.origin = origin
        self.call = call
        self.invisible = invisible

    def __copy__(self):
        if self.invisible:
            if hasattr(self.curve, '__copy__'):
                return self.curve.__copy__()
            return self.curve.__class__(self.curve)
        args, kwargs = attr(self, 'curve')
        return self.__class__(*args, **kwargs)

    def __str__(self):
        if self.invisible:
            return str(self.curve)
        return repr_attr(self, 'curve', rstyle=False)

    def __repr__(self):
        if self.invisible:
            return repr(self.curve)
        return repr_attr(self, 'curve')

    def __bool__(self):
        return bool(self.curve)

    def __getitem__(self, item):
        return self.curve[self._f(item)]

    def __setitem__(self, key, value):
        self.curve[self._f(key)] = value

    def __delitem__(self, key):
        del self.curve[self._f(key)]

    def __iter__(self):
        return iter(map(self._g, self.curve))

    def __contains__(self, item):
        return self._f(item) in self.curve

    def __call__(self, *_, **__):
        _ = tuple(self._f(v) for v in _)
        __ = dict((k, self._f(v)) for k, v in __.items())

        if self.call is None:
            return self.curve(*_, **__)
        if callable(self.call):
            return self.call(self.curve, *_, **__)
        return getattr(self.curve, self.call)(*_, **__)

    def _f(self, x):
        """transform arguments into real float values"""
        return x if self.origin is None else x - self.origin

    def _g(self, y):
        """transform real float arguments into values"""
        return y if self.origin is None else self.origin + y


class float_curve(curve_wrapper):

    def __init__(self, curve=0.0, origin=None):
        super().__init__(curve, origin=origin, invisible=True)

    def __float__(self):
        return float(self.curve)

    def __eq__(self, other):
        return other == float(self.curve)

    def __getitem__(self, item):
        return self.curve

    def __setitem__(self, key, value):
        self.curve = value

    def __delitem__(self, key):
        self.curve = 0.0

    def __call__(self, *_, **__):
        return self.curve

    def __iter__(self):
        return iter([self.origin])


class curve_algebra(curve_wrapper):
    """algebraic operations on curves

    (c1 + ... + cn)
    * m1 * ... * mk / d1 / ... / dl
    + a1 + ... at - s1 - ... - sr"""

    def __init__(self, curve, add=(), sub=(), mul=(), div=(), inplace=False):
        self._inplace = inplace
        self.spread = 0.0
        self.leverage = 1.0
        self.add = [init_curve(curve) for curve in add]
        self.sub = [init_curve(curve) for curve in sub]
        self.mul = [init_curve(curve) for curve in mul]
        self.div = [init_curve(curve) for curve in div]

        if isinstance(curve, curve_algebra):
            self.spread = curve.spread
            self.leverage = curve.leverage
            self.add.extend(curve.add)
            self.sub.extend(curve.sub)
            self.mul.extend(curve.mul)
            self.div.extend(curve.div)
            curve = curve.curve

        super().__init__(curve)

    def __call__(self, *_, **__):
        r = self.curve(*_, **__)
        r *= prod(m(*_, **__) for m in self.mul)
        r /= prod(d(*_, **__) for d in self.div)
        r += sum(a(*_, **__) for a in self.add)
        r -= sum(s(*_, **__) for s in self.sub)
        return self.spread + self.leverage * r

    def __add__(self, other):
        curve = self if self._inplace else self.__copy__()
        other = init_curve(other)
        if other in curve.sub:
            curve.sub.pop(curve.sub.index(other))
        else:
            curve.add.append(other)
        return curve

    def __sub__(self, other):
        curve = self if self._inplace else self.__copy__()
        other = init_curve(other)
        if other in curve.add:
            curve.add.pop(curve.add.index(other))
        else:
            curve.sub.append(other)
        return curve

    def __mul__(self, other):
        curve = self if self._inplace else self.__copy__()
        other = init_curve(other)
        if other in curve.div:
            curve.div.pop(curve.div.index(other))
        else:
            curve.mul.append(other)
        return curve

    def __truediv__(self, other):
        curve = self if self._inplace else self.__copy__()
        other = init_curve(other)
        if other in curve.mul:
            curve.mul.pop(curve.mul.index(other))
        else:
            curve.div.append(other)
        return curve

    def __str__(self):
        return repr_algebra(
            self.curve, self.mul, self.div, self.add, self.sub, rstyle=False)

    def __repr__(self):
        return repr_algebra(self.curve, self.mul, self.div, self.add, self.sub)


# --- curve_wrapper builder functions ---


def init_curve(curve):
    if isinstance(curve, (int, float)):
        curve = float_curve(curve)
    if isinstance(curve, curve_wrapper):
        return curve
    return curve_wrapper(curve, invisible=True)


def generate_call_wrapper(name, function=None):
    """generate multiple call_wrapper subtypes by names"""
    return type(name, (curve_wrapper,), {'call': function or name})


def interpolation_builder(x_list, y_list, interpolation):
    # gather interpolation
    if isinstance(interpolation, str):
        i_type = getattr(_interpolation, interpolation)
    else:
        i_type = interpolation
        interpolation = getattr(i_type, '__name__', str(i_type))
    new = curve_wrapper(i_type(x_list, y_list), invisible=True)
    new.interpolation = interpolation
    return new


# --- DomainCurve class ---


class DomainCurve(curve_wrapper):

    def __init__(self, domain=(), curve=(), interpolation=linear,
                 origin=None, day_count=None, date_type=None):
        """
        :param curve: underlying curve
        :param day_count: function to calculate year fractions
            (time between dates as a float)
        :param origin: origin date of curve
        :param curve_type:
        :param **kwargs:
        """

        self.domain = domain
        self.day_count = day_count

        # re-use curve
        if isinstance(curve, DomainCurve):
            day_count = curve.day_count if day_count is None else day_count
            origin = curve.origin if origin is None else origin
            domain = curve.domain if not domain else domain
            curve = curve.curve

        # gather date type
        if date_type is None:
            date_type = None if origin is None else type(origin)

        # gather origin
        if origin is None:
            if date_type is None:
                origin = 0.0
            elif hasattr(date_type, 'today'):
                origin = date_type.today()
            else:
                origin = date_type()

        # either re-use curve
        if callable(curve) or isinstance(curve, (int, float)):
            curve = init_curve(curve)

        # or build curve
        else:
            self.origin = origin
            self.day_count = day_count
            yf_domain = type(domain)(self._f(d) for d in domain)
            curve = init_curve(interpolation(yf_domain, curve))

        super().__init__(curve, origin=origin)
        self.domain = domain
        self.day_count = day_count

    def __iter__(self):
        if not self.domain:
            return iter(super())
        return iter(self.domain)

    def _f(self, x):
        if self.day_count is None:
            # if hasattr(self.origin, 'day_count'):
            #     return self.origin.day_count(x)
            return _day_count (self.origin, x)
        return self.day_count(self.origin, x)
