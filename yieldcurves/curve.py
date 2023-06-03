from math import prod
from vectorizeit import vectorize

from .tools import attr, repr_attr, repr_algebra, ascii_plot

from .daycount import day_count as _day_count
from .interpolation import linear
from . import interpolation as _interpolation


# --- base curve classes ---


class CurveWrapper:

    def __init__(self, curve, call=None, invisible=None):
        self.curve = curve
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

    def keys(self):
        return self.curve.keys()

    def values(self):
        return self.curve.values()

    def items(self):
        return self.curve.items()

    def pop(self, item):
        return self.pop(item)

    def update(self, data):
        return self.curve.update(data)

    @vectorize()
    def __call__(self, *_, **__):
        _ = tuple(self._f(v) for v in _)
        __ = dict((k, self._f(v)) for k, v in __.items())

        if self.call is None:
            r = self.curve(*_, **__)
        elif callable(self.call):
            r = self.call(self.curve, *_, **__)
        else:
            r = getattr(self.curve, self.call)(*_, **__)
        return r

    @vectorize()
    def _f(self, x, y=None):
        """transform arguments into real float values"""
        if x is None:
            return None
        if y is None:
            return x
        return y - x

    @vectorize()
    def _g(self, x, y=None):
        """transform real float arguments into values"""
        if x is None:
            return None
        if y is None:
            return x
        return x + y

    def plot(self, x=()):
        if not x:
            x = [0.01 * i for i in range(100)]
        ascii_plot(x, self)


class ConstantCurve(CurveWrapper):

    def __init__(self, curve=0.0):
        super().__init__(curve, invisible=True)

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

    def __iter__(self):
        return iter([None])

    @vectorize()
    def __call__(self, *_, **__):
        return self.curve


class CurveAlgebra(CurveWrapper):
    """algebraic operations on curves

    (c1 + ... + cn)
    * m1 * ... * mk / d1 / ... / dl
    + a1 + ... at - s1 - ... - sr"""

    def __init__(self, curve, add=(), sub=(), mul=(), div=(),
                 spread=None, leverage=None, inplace=False,
                 call=None, invisible=False):
        self._inplace = inplace

        if isinstance(curve, CurveAlgebra):
            spread = curve.spread if spread is None else spread
            leverage = curve.leverage if leverage is None else leverage
            add.extend(curve.add)
            sub.extend(curve.sub)
            mul.extend(curve.mul)
            div.extend(curve.div)
            curve = curve.curve

        self.spread = spread
        self.leverage = leverage
        self.add = [init_curve(a) for a in add]
        self.sub = [init_curve(s) for s in sub]
        self.mul = [init_curve(m) for m in mul]
        self.div = [init_curve(d) for d in div]

        super().__init__(curve, call=call, invisible=invisible)

    @vectorize()
    def __call__(self, *_, **__):
        r = super().__call__(*_, **__)
        r *= prod(m(*_, **__) for m in self.mul)
        r /= prod(d(*_, **__) for d in self.div)
        r += sum(a(*_, **__) for a in self.add)
        r -= sum(s(*_, **__) for s in self.sub)

        spread = 0.0 if self.spread is None else self.spread
        leverage = 1.0 if self.leverage is None else self.leverage
        return spread + leverage * r

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
        curve = ConstantCurve(curve)
    if isinstance(curve, CurveWrapper):
        return curve
    return CurveWrapper(curve, invisible=True)


def call_wrapper(name, function=None):
    """generate call_wrapper subtypes by names"""
    return type(name, (CurveWrapper,), {'call': function or name})


def interpolation_builder(x_list, y_list, interpolation, **__):
    # gather interpolation
    if isinstance(interpolation, str):
        i_type = getattr(_interpolation, interpolation)
    else:
        i_type = interpolation
        interpolation = getattr(i_type, '__name__', str(i_type))
    new = CurveWrapper(i_type(x_list, y_list, **__), invisible=True)
    new.interpolation = interpolation
    return new


# --- DomainCurve class ---


class DomainCurve(CurveWrapper):

    date_type = float

    @classmethod
    def interpolated(cls, domain=(), data=(), interpolation=linear,
                     origin=None, day_count=None, **__):
        # init instance
        self = cls(curve=(), domain=domain, origin=origin, day_count=day_count)
        # transform domain and build inner curve
        f_domain = tuple(self._f(d) for d in self.domain)
        self.curve = interpolation_builder(f_domain, data, interpolation, **__)
        return self

    def __init__(self, curve=(), domain=(), origin=None, day_count=None,
                 call=None, invisible=False):

        domain = tuple(domain)

        # gather origin
        if origin is None:
            if domain:
                origin = domain[0]
            else:
                date_type = self.__class__.date_type
                if hasattr(date_type, 'today'):
                    origin = date_type.today()
                else:
                    origin = date_type()

        self.origin = origin
        self.domain = domain
        self.day_count = day_count

        # re-use curve
        if isinstance(curve, DomainCurve):
            day_count = curve.day_count if day_count is None else day_count
            origin = curve.origin if origin is None else origin
            domain = curve.domain if not domain else domain
            curve = curve.curve

        self.origin = origin
        self.domain = domain
        self.day_count = day_count

        super().__init__(init_curve(curve), call=call, invisible=invisible)

    def __iter__(self):
        if not self.domain:
            return iter(super())
        return iter(self.domain)

    @vectorize()
    def _f(self, x, y=None):
        """transform arguments into real float values"""
        if x is None:
            return None
        if y is None:
            x, y = self.origin, x
        if self.day_count is None:
            # if hasattr(self.origin, 'day_count'):
            #     return self.origin.day_count(x)
            return _day_count (x, y)
        return self.day_count(x, y)

    @vectorize()
    def _g(self, x, y=None):
        """transform real float arguments into values"""
        raise NotImplemented()
