# -*- coding: utf-8 -*-

# yieldcurves
# -----------
# A Python library for financial yield curves.
#
# Author:   sonntagsgesicht
# Version:  0.1, copyright Saturday, 22 April 2023
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


from math import prod

from vectorizeit import vectorize
from .pp import pretty


@pretty
class AlgebraCurve:
    """algebraic operations on curves

    (c1 + ... + cn)
    * m1 * ... * mk / d1 / ... / dl
    + a1 + ... at - s1 - ... - sr"""
    __slots__ = 'curve', 'add', 'sub', 'mul', 'div', 'pre', \
        'spread', 'leverage', 'multiplier', 'inplace'

    def __init__(self, curve=None, *, add=[], sub=[], mul=[], div=[], pre=[],
                 spread=0.0, leverage=1.0, multiplier=1.0, inplace=False):
        self.curve = curve

        self.add = list(add)
        self.sub = list(sub)
        self.mul = list(mul)
        self.div = list(div)
        self.pre = list(pre)
        self.spread = spread
        self.leverage = leverage
        self.multiplier = multiplier

        self.inplace = inplace

    def __copy__(self):
        kwargs = {k: getattr(self, k) for k in self.__slots__}
        return self.__class__(**kwargs)

    @vectorize()
    def __call__(self, x):

        for p in self.pre:
            x = p(x) if callable(p) else p

        if self.curve is None:
            r = x
        elif callable(self.curve):
            r = self.curve(x)
        else:
            r = self.curve

        r *= prod(m(x) if callable(m) else m for m in self.mul)
        r /= prod(d(x) if callable(d) else d for d in self.div)
        r += sum(a(x) if callable(a) else a for a in self.add)
        r -= sum(s(x) if callable(s) else s for s in self.sub)

        return (self.spread + self.leverage * r) * self.multiplier

    def x__getattr__(self, item):
        if hasattr(self.curve, item):
            def func(*args, **kwargs):
                args = tuple(self.year_fraction(x) for x in args)
                kwargs = {k: self.year_fraction(y) for k, y in kwargs.items()}
                return getattr(self.curve, item)(*args, **kwargs)
            func.__qualname__ = self.__class__.__qualname__ + '.' + item
            func.__name__ = item
            return func
        msg = f"{self.__class__.__name__!r} object has no attribute {item!r}"
        raise AttributeError(msg)

    def __neg__(self):
        curve = self if self.inplace else self.__copy__()
        curve.multiplier *= -1
        return curve

    def __add__(self, other):
        curve = self if self.inplace else self.__copy__()
        if other in curve.sub:
            curve.sub.pop(curve.sub.index(other))
        else:
            curve.add.append(other)
        return curve

    def __radd__(self, other):
        return AlgebraCurve(other) + self

    def __sub__(self, other):
        curve = self if self.inplace else self.__copy__()
        if other in curve.add:
            curve.add.pop(curve.add.index(other))
        else:
            curve.sub.append(other)
        return curve

    def __rsub__(self, other):
        return AlgebraCurve(other) - self

    def __mul__(self, other):
        curve = self if self.inplace else self.__copy__()
        if other in curve.div:
            curve.div.pop(curve.div.index(other))
        else:
            curve.mul.append(other)
        return curve

    def __rmul__(self, other):
        return AlgebraCurve(other) * self

    def __truediv__(self, other):
        curve = self if self.inplace else self.__copy__()
        if other in curve.mul:
            curve.mul.pop(curve.mul.index(other))
        else:
            curve.div.append(other)
        return curve

    def __rtruediv__(self, other):
        return AlgebraCurve(other) / self

    def __pos__(self):
        raise NotImplementedError()

    def __pow__(self, other):
        raise NotImplementedError()

    def __abs__(self):
        raise NotImplementedError()

    def __matmul__(self, other):
        curve = self if self.inplace else self.__copy__()
        curve.pre.append(other)
        return curve

    def __rmatmul__(self, other):
        return AlgebraCurve(other) @ self
