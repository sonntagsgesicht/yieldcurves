from typing import Union, Callable, Iterable
from math import prod
from vectorizeit import vectorize

from .repr import attr, repr_attr

Curve = Union[float, Callable]


# --- base curve classes ---


class CurveAdapter:

    def __init__(self, curve: Curve, *,
                 invisible: bool = None):
        r"""Wrapper class for a curve (i.e. callable)

        :param curve: inner curve object $\phi: X \to Y$ to wrap around.
            This argument can be a single value $v$ which results in constant
            function $\phi(x)=v$.
        :param invisible: boolean flag to control string representation.
            If **True** both **str** and **repr** is forwarded to **curve**.
            (optional, default is **False** if **curve** is callable
            else **True**)

        """
        self.curve = curve
        self.invisible = invisible

        if invisible is None and not callable(curve):
            # view constant curve as a constant value
            self.invisible = True

    def __copy__(self):
        _, kwargs = attr(self)
        if hasattr(self.curve, '__copy__'):
            kwargs['curve'] = self.curve.__copy__()
        return self.__class__(**kwargs)

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

    def __float__(self):
        return float(self.curve)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.curve == other.curve
        return False

    @vectorize()
    def __call__(self, *_, **__):
        if callable(self.curve):
            return self.curve(*_, **__)
        return self.curve

    def __getitem__(self, item):
        if hasattr(self.curve, '__getitem__'):
            return self.curve.__getitem__(item)

    def __setitem__(self, key, value):
        if hasattr(self.curve, '__setitem__'):
            return self.curve.__setitem__(key, value)

    def __delitem__(self, key):
        if hasattr(self.curve, '__delitem__'):
            return self.curve.__delitem__(key)

    def __iter__(self):
        if hasattr(self.curve, '__iter__'):
            return self.curve.__iter__()
        return iter(tuple())

    def __len__(self):
        if hasattr(self.curve, '__len__'):
            return self.curve.__len__()
        return 0

    def __contains__(self, item):
        return item in self.curve

    def keys(self):
        if hasattr(self.curve, 'keys'):
            return self.curve.keys()
        return ()

    def values(self):
        if hasattr(self.curve, 'values'):
            return self.curve.values()
        return ()

    def items(self):
        if hasattr(self.curve, 'items'):
            return self.curve.items()
        return ()

    def pop(self, item):
        if hasattr(self.curve, 'pop'):
            return self.curve.pop(item)

    def update(self, data):
        if hasattr(self.curve, 'update'):
            return self.curve.update(data)

    def get(self, item, default=None):
        if hasattr(self.curve, 'get'):
            return self.curve.get(item, default)


class CallAdapter(CurveAdapter):

    def __init__(self, curve: Curve, *,
                 invisible: bool = None,
                 call: Union[str, Callable] = None):
        r"""Wrapper class for a curve (i.e. callable)

        :param curve: inner curve object $\phi: X \to Y$ to wrap around.
            This argument can be a single value $v$ which results in constant
            function $\phi(x)=v$.
        :param invisible: boolean flag to control string representation.
            If **True** both **str** and **repr** is forwarded to **curve**.
            (optional, default is **False** if **curve** is callable
            else **True**)
        :param call: name of method of to be invoked when wrapper is invoked
            via **__call__**
            (optional, default is **__call__**)

        """
        super().__init__(curve, invisible=invisible)
        self.call = call or getattr(self.__class__, 'call', None)

    @vectorize()
    def __call__(self, *_, **__):
        if callable(self.call):
            return self.call(self.curve, *_, **__)
        _attr = getattr(self.curve, str(self.call), self.curve)
        if callable(_attr):
            return _attr(*_, **__)
        return _attr


class CurveAlgebra(CurveAdapter):
    """algebraic operations on curves

    (c1 + ... + cn)
    * m1 * ... * mk / d1 / ... / dl
    + a1 + ... at - s1 - ... - sr"""

    def __init__(self,
                 curve: Union[Curve, CurveAdapter],
                 *,
                 add: Iterable[Union[Curve, CurveAdapter]] = (),
                 sub: Iterable[Union[Curve, CurveAdapter]] = (),
                 mul: Iterable[Union[Curve, CurveAdapter]] = (),
                 div: Iterable[Union[Curve, CurveAdapter]] = (),
                 spread: float = None,
                 leverage: float = None,
                 inplace: bool = False,
                 invisible: bool = False):
        """

        :param curve:
        :param add:
        :param sub:
        :param mul:
        :param div:
        :param spread:
        :param leverage:
        :param inplace:
        :param invisible:
        """
        self._inplace = inplace

        if isinstance(curve, CurveAlgebra):
            spread = curve.spread if spread is None else spread
            leverage = curve.leverage if leverage is None else leverage
            add = list(add) + curve.add
            sub = list(sub) + curve.sub
            mul = list(mul) + curve.mul
            div = list(div) + curve.div
            curve = curve.curve

        self.spread = spread
        self.leverage = leverage
        self.add = [init_curve(a) for a in add]
        self.sub = [init_curve(s) for s in sub]
        self.mul = [init_curve(m) for m in mul]
        self.div = [init_curve(d) for d in div]

        super().__init__(init_curve(curve), invisible=invisible)

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
        # return x * m*...*m / d/.../d + a+...+a - s-...-s
        x = str(self.curve)
        x += ' * ' + ' * '.join(map(str, self.mul)) if self.mul else ''
        x += ' / ' + ' / '.join(map(str, self.div)) if self.div else ''
        x += ' + ' + ' + '.join(map(str, self.add)) if self.add else ''
        x += ' - ' + ' - '.join(map(str, self.sub)) if self.sub else ''
        return x

    def __repr__(self):
        # return x * m*...*m / d/.../d + a+...+a - s-...-s
        x = repr(self.curve)
        x += ' * ' + ' * '.join(map(repr, self.mul)) if self.mul else ''
        x += ' / ' + ' / '.join(map(repr, self.div)) if self.div else ''
        x += ' + ' + ' + '.join(map(repr, self.add)) if self.add else ''
        x += ' - ' + ' - '.join(map(repr, self.sub)) if self.sub else ''
        return x


# --- curve_wrapper builder functions ---


def init_curve(curve: Curve, curve_type=CurveAdapter):
    if isinstance(curve, curve_type):
        return curve
    return curve_type(curve, invisible=True)


def call_wrapper_builder(name: str, function: str = None) -> type:
    """generate call_wrapper subtypes by names"""
    return type(name, (CallAdapter,), {'call': function or name})