# -*- coding: utf-8 -*-

# yieldcurves
# -----------
# A Python library for financial yield curves.
#
# Author:   sonntagsgesicht
# Version:  0.2.6.1, copyright Monday, 14 October 2024
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


from bisect import bisect_left, bisect_right
from collections import UserDict
from copy import copy
from functools import partial
from math import exp, log
from reprlib import Repr
# from typing import Dict, Iterable, Callable, Tuple

from .tools import Curve, bisection_method, newton_raphson, secant_method
from .tools import prettyclass


_repr = Repr()
_repr.maxlist = _repr.maxtuple = 1
_repr.maxset = _repr.maxfrozenset = 1
_repr.maxdict = 1
_repr.maxsting = _repr.maxother = 40


def fit(curve,
        grid,  # grid: Iterable[float],
        err_func,  # err_func: Callable | Iterable[Callable],
        target_list=None,  # target_list: Iterable[float] | None = None,
        interpolation_type=None,  # interpolation_type: str | Callable | None = None,  # noqa E501
        method='secant_method',  # method; str = 'secant_method'
        bounds=(-0.1, 0.2),  # bounds: Tuple[float, float] = (-0.1, 0.2),
        tolerance=1e-10,  # tolerance: float = 1e-10,
        ):  # ) -> Dict[float, float]:
    """ fit according to calibration routine to target values

    >>> from functools import partial
    >>> from yieldcurves import YieldCurve
    >>> from yieldcurves.interpolation import fit

    >>> yc = YieldCurve(0.0)
    >>> grid = [1., 1.8, 2., 2.34]
    >>> err_func = [partial(yc.df, t) for t in grid]
    >>> # equivalent to err_func = yc.df
    >>> targets =  [0.94, 0.93, 0.92, 0.91]

    >>> fit(yc.curve, grid, err_func, targets)
    {1.0: 0.06187540363412898, 1.8: 0.040317051604091554, 2.0: 0.04169080450970588, 2.34: 0.040303709259234204}

    """  # noqa E501
    grid = tuple(grid)
    if callable(err_func):
        err_func = [partial(err_func, x) for x in grid]
    if target_list is None:
        target_list = [0.0] * len(grid)
    if interpolation_type is None:
        func = piecewise_linear
    elif isinstance(interpolation_type, str):
        func = globals()[interpolation_type]
    else:
        func = interpolation_type

    # check iadd/isub of curve
    if not isinstance(curve, Curve):
        _curve = copy(curve)
        _val = 0.01
        _addon = func(grid, [_val] * len(grid))
        _vals = {x: _curve(x) for x in grid}
        _curve += _addon
        _vals2 = [abs(_curve(x) - _val - v) for x, v in _vals.items()]
        _curve -= _addon
        _vals3 = [abs(_curve(x) - v) for x, v in _vals.items()]

        if max(_vals2) + max(_vals3) < tolerance:
            msg = (f"fit requires proper inplace add and sub of curves "
                   f"but failed for {curve}")
            raise TypeError(msg)

    # move on to curve fitting
    addon = func(grid, [0.0] * len(grid))
    curve += addon
    for t, f, v in zip(grid, err_func, target_list):
        # set error function
        def err(current):
            addon[t] = current
            return f() - v
        # run root finding

        if 'newton' in method:
            guess = sum(bounds) / 2
            newton_raphson(err, guess, tolerance)
        elif 'secant' in method:
            a, b = sum(bounds) / 3, sum(bounds) / 2
            secant_method(err, a, b, tolerance)
        elif 'bisec' in method:
            a, b = bounds
            bisection_method(err, a, b, tolerance)
        else:
            raise ValueError(f"unkown method {method}")

    curve -= addon
    return dict(addon.items())


class plist(list):
    """pretty print list"""

    def __str__(self):
        return _repr.repr(list(self))


@prettyclass(init=False)
class base_interpolation(UserDict):
    """
    Basic class to interpolate given data.
    """

    @property
    def x_list(self):
        return plist(self.keys())

    @property
    def y_list(self):
        return plist(self.values())

    def __init__(self, x_list=(), y_list=()):
        r""" interpolation class

        :param x_list: points $x_1 \dots x_n$
        :param y_list: values $y_1 \dots y_n$

        """
        # new implementation since dicts are ordered in Python 3.8
        if not len(set(x_list)) == len(x_list):
            raise KeyError(f"identical x values in {x_list}")
        # super().__init__(sorted(zip(x_list, y_list)))
        if callable(y_list):
            y_list = tuple(y_list(x) for x in x_list)
        if isinstance(x_list, dict) and not y_list:
            y_list = x_list.values()
            x_list = x_list.keys()
        super().__init__(zip(map(float, x_list), map(float, y_list)))

    def __call__(self, x):
        return float(x)

    def __setitem__(self, key, value):
        super().__setitem__(float(key), float(value))
        self.data = dict(sorted(self.data.items()))

    def _op(self, other, attr):
        new = self.__copy__()
        if not callable(other):
            other = constant([0.0], [other])
        for k in new:
            new[k] = getattr(new[k], attr)(other(k))
        return new

    def __add__(self, other):
        return self._op(other, '__add__')

    def __sub__(self, other):
        return self._op(other, '__sub__')

    def __mul__(self, other):
        return self._op(other, '__mul__')

    def __truediv__(self, other):
        return self._op(other, '__truediv__')


class flat(base_interpolation):
    def __init__(self, y=0.0):
        r""" flat or constant interpolation

        :param y: constant return float $\hat{y}$

        A |flat()| object is a function $f$
        returning a constant float $\hat{y}$.
        $$f(x)=\hat{y}\text{ const.}$$
        for all $x$.

        >>> from yieldcurves.interpolation import flat
        >>> c = flat(1.1)
        >>> c(0)
        1.1
        >>> c(2.1)
        1.1

        """
        super(flat, self).__init__([0.0], [y])

    def __call__(self, x):
        return self.y_list[0]


class identity(base_interpolation):

    pass


class _default_value_interpolation(base_interpolation):

    def __init__(self, x_list=(), y_list=(), default_value=None):
        r""" default float interpolation

        :param x_list: points $x_1 \dots x_n$
        :param y_list: values $y_1 \dots y_n$
        :param default_value: default float $d$

        A |default_value_interpolation()| object is a function $f$
        returning at $x$ the float $y_i$
        with $i$ to be the first matching index such that $x=x_i$
        $$f(x)=y_i\text{ for } x=x_i$$
        and $d$ if no matching $x_i$ is found.

        >>> from yieldcurves.interpolation import _default_value_interpolation
        >>> # c = _default_value_interpolation([1,2,3,1], [1,2,3,4], default_value=42)
        >>> c = _default_value_interpolation([1,2,3], [1,2,3], default_value=42)
        >>> c(1)
        1.0
        >>> c(2)
        2.0
        >>> c(4)
        42

        """  # noqa 501
        self._default = default_value
        super().__init__(x_list, y_list)

    def __call__(self, x):
        if x not in self.x_list:
            return self._default
        return self.y_list[self.x_list.index(x)]


class no(_default_value_interpolation):
    def __init__(self, x_list=(), y_list=()):
        r""" no interpolation at all

        :param x_list: points $x_1 \dots x_n$
        :param y_list: values $y_1 \dots y_n$

        A |no()| object is a function $f$
        returning at $x$ the float $y_i$
        with $i$ to be the first matching index such that $x=x_i$
        $$f(x)=y_i\text{ for } x=x_i \text{ else None}$$

        >>> from yieldcurves.interpolation import no
        >>> # c = no([1,2,3,1], [1,2,3,4])
        >>> c = no([1,2,3], [1,2,3])
        >>> c(1)
        1.0
        >>> c(2)
        2.0
        >>> c(4)

        """
        super().__init__(x_list, y_list)


class zero(_default_value_interpolation):
    def __init__(self, x_list=(), y_list=()):
        r""" interpolation by filling with zeros between points

        :param x_list: points $x_1 \dots x_n$
        :param y_list: values $y_1 \dots y_n$

        A |zero()| object is a function $f$
        returning at $x$ the float $y_i$
        if $x=x_i$ else zero.
        with $i$ to be the first matching index such that
        $$f(x)=y_i\text{ for } x=x_i \text{ else } 0$$


        >>> from yieldcurves.interpolation import zero
        >>> # c = zero([1,2,3,1], [1,2,3,4])
        >>> c = zero([1,2,3], [1,2,3])
        >>> c(1)
        1.0
        >>> c(1.1)
        0.0
        >>> c(2)
        2.0
        >>> c(4)
        0.0
        """
        super().__init__(x_list, y_list, 0.0)


class left(base_interpolation):

    def __init__(self, x_list=(), y_list=()):
        r""" left interpolation

        :param x_list: points $x_1 \dots x_n$
        :param y_list: values $y_1 \dots y_n$

        A |left()| object is a function $f$
        returning at $x$ the last given float $y_i$
        reading from left to right, i.e.
        with $i$ to be the matching index such that
        $$f(x)=y_i\text{ for } x_i \leq x < x_{i+1}$$
        or $y_1$ if $x<x_1$.

        >>> from yieldcurves.interpolation import left
        >>> c = left([1,3], [1,2])
        >>> c(0)
        1.0
        >>> c(1)
        1.0
        >>> c(2)
        1.0
        >>> c(4)
        2.0
        """
        super().__init__(x_list, y_list)

    def __call__(self, x):
        if len(self.y_list) == 0:
            raise OverflowError
        if x in self.x_list:
            i = self.x_list.index(x)
        else:
            i = bisect_left(self.x_list, float(x), 1,
                            len(self.x_list)) - 1
        return self.y_list[i]


class constant(left):
    def __init__(self, x_list=(), y_list=()):
        r""" constant interpolation

        :param x_list: points $x_1 \dots x_n$
        :param y_list: values $y_1 \dots y_n$

        Same as |left()|.
        """
        super().__init__(x_list, y_list)


class right(base_interpolation):

    def __init__(self, x_list=(), y_list=()):
        r""" right interpolation

        :param x_list: points $x_1 \dots x_n$
        :param y_list: values $y_1 \dots y_n$

        A |right()| object is a function $f$
        returning at $x$ the last given float $y_i$
        reading from right to left, i.e.
        with $i$ to be the matching index such that
        $$f(x)=y_i\text{ for } x_i < x \leq x_{i+1}$$
        or $y_n$ if $x_n < x$.

        >>> from yieldcurves.interpolation import right
        >>> c = right([1,3], [1,2])
        >>> c(0)
        1.0
        >>> c(1)
        1.0
        >>> c(2)
        2.0
        >>> c(4)
        2.0
        """
        super().__init__(x_list, y_list)

    def __call__(self, x):
        if len(self.y_list) == 0:
            raise OverflowError
        if x in self.x_list:
            i = self.x_list.index(x)
        else:
            i = bisect_right(self.x_list, float(x), 0,
                             len(self.x_list) - 1)
        return self.y_list[i]


class nearest(base_interpolation):
    def __init__(self, x_list=(), y_list=()):
        r""" nearest interpolation

        :param x_list: points $x_1 \dots x_n$
        :param y_list: values $y_1 \dots y_n$

        A |nearest()| object is a function $f$
        returning at $x$ the given float $y_i$
        of the nearest $x_i$
        from both left and right, i.e.
        with $i$ to be the matching index such that
        $$f(x)=y_i \text{ for } \mid x_i -x \mid  = \min_j \mid x_j -x \mid$$

        >>> from yieldcurves.interpolation import nearest
        >>> c = nearest([1,2,3], [1,2,3])
        >>> c(0)
        1.0
        >>> c(1)
        1.0
        >>> c(1.5)
        1.0
        >>> c(1.51)
        2.0
        >>> c(2)
        2.0
        >>> c(4)
        3.0
        """
        super().__init__(x_list, y_list)

    def __call__(self, x):
        if len(self.y_list) == 0:
            raise OverflowError
        if len(self.y_list) == 1:
            return self.y_list[0]
        if x in self.x_list:
            i = self.x_list.index(x)
        else:
            i = bisect_left(self.x_list, float(x), 1, len(self.x_list) - 1)
            if (self.x_list[i - 1] - x) / (self.x_list[i - 1] -
                                           self.x_list[i]) <= 0.5:
                i -= 1
        return self.y_list[i]


class linear(base_interpolation):

    def __init__(self, x_list=(), y_list=()):
        r""" linear interpolation

        :param x_list: points $x_1 \dots x_n$
        :param y_list: values $y_1 \dots y_n$

        A |linear()| object is a function $f$
        returning at $x$ the linear interpolated float of
        $y_i$ and $y_{i+1}$ when $x_i \leq x < x_{i+1}$, i.e.
        $$f(x)=(y_{i+1}-y_i) \cdot \frac{x-x_i}{x_{i+1}-x_i}$$

        >>> from yieldcurves.interpolation import linear
        >>> c = linear([1,2,3], [2,3,4])
        >>> c(0)
        1.0
        >>> c(1)
        2.0
        >>> c(1.5)
        2.5
        >>> c(1.51)
        2.51
        >>> c(2)
        3.0
        >>> c(4)
        5.0
        """
        super().__init__(x_list, y_list)

    def __call__(self, x):
        if len(self.y_list) == 0:
            raise OverflowError(f'x_list={self.x_list} y_list={self.y_list}')
        if len(self.y_list) == 1:
            return self.y_list[0]
        i = bisect_left(self.x_list, float(x), 1, len(self.x_list) - 1)
        return self.y_list[i - 1] + (self.y_list[i] - self.y_list[i - 1]) * \
            (self.x_list[i - 1] - x) / (self.x_list[i - 1] - self.x_list[i])


class piecewise_linear(linear):

    def __init__(self, x_list=(), y_list=()):
        r"""piecewise linear curve

        :param x_list: points $x_1 \dots x_n$
        :param y_list: values $y_1 \dots y_n$

        A |piecewise_linear()| object is a function $f$
        returning at $x$ the linear interpolated float of
        $y_i$ and $y_{i+1}$ when $x_i \leq x < x_{i+1}$, i.e.
        $$f(x)=(y_{i+1}-y_i) \cdot \frac{x-x_i}{x_{i+1}-x_i}$$

        and

        $y_1$ if $x \leq x_1$

        as well as

        $y_n$ if $x_n <x$.


        >>> from yieldcurves.interpolation import piecewise_linear
        >>> c = piecewise_linear([1.,2.,3.], [2.,3.,4.])
        >>> c(0.)
        2.0
        >>> c(1.)
        2.0
        >>> c(1.5)
        2.5
        >>> c(1.51)
        2.51
        >>> c(2.)
        3.0
        >>> c(3.)
        4.0
        >>> c(4)
        4.0
        """
        super().__init__(x_list, y_list)

    def __call__(self, x):
        if not self:
            cls = self.__class__.__name__
            raise ValueError(f"{cls} must contain at least one point")
        x = float(x)
        if len(self) == 1 or x <= self.x_list[0]:
            return self.y_list[0]
        if self.x_list[-1] <= x:
            return self.y_list[-1]
        return super().__call__(x)


class loglinear(linear):
    def __init__(self, x_list=(), y_list=()):
        r""" log-linear interpolation

        :param x_list: points $x_1 \dots x_n$
        :param y_list: values $y_1 \dots y_n$

        A |loglinear()| object is a function $f$
        returning at $x$ the float $\exp(y)$
        of  the linear interpolated float $y$ of
        $\log(y_i)$ and $\log(y_{i+1})$ when $x_i \leq x < x_{i+1}$, i.e.
        $$f(x)=\exp\Big((\log(y_{i+1})-\log(y_i))
        \cdot \frac{x-x_i}{x_{i+1}-x_i}\Big)$$

        >>> from math import log, exp
        >>> from yieldcurves.interpolation import loglinear
        >>> c = loglinear([1,2,3], [exp(2),exp(3),exp(4)])
        >>> log(c(0))
        1.0
        >>> log(c(1))
        2.0
        >>> log(c(1.5))
        2.5
        >>> log(c(1.51))
        2.51
        >>> log(c(2))
        3.0
        >>> log(c(4))
        5.0

        .. note::

            **loglinear** requires strictly positive values $0<y_1 \dots y_n$.

        """
        if not all(0. < y for y in y_list):
            raise ValueError('log interpolation requires positive values.')
        log_y_list = [log(y) for y in y_list]
        super(loglinear, self).__init__(x_list, log_y_list)

    def __call__(self, x):
        log_y = super(loglinear, self).__call__(x)
        return exp(log_y)


class loglinearrate(linear):
    def __init__(self, x_list=(), y_list=()):
        r""" log-linear interpolation by annual rates

        :param x_list: points $x_1 \dots x_n$
        :param y_list: values $y_1 \dots y_n$

        A |loglinearrate()| object is a function $f$
        returning at $x$ the float $\exp(x \cdot y)$
        of  the linear interpolated float $y$ of
        $\log(\frac{y_i}{x_i})$ and $\log(\frac{y_{i+1}}{x_{i+1}})$
        when $x_i \leq x < x_{i+1}$, i.e.
        $$f(x)=\exp\Big(x \cdot
        (\log(\frac{y_{i+1}}{x_{i+1}})-\log(\frac{y_i}{x_i}))
        \cdot \frac{x-x_i}{x_{i+1}-x_i}\Big)$$

        >>> from math import log, exp
        >>> from yieldcurves.interpolation import loglinear
        >>> c = loglinear([1,2,3], [exp(1*2),exp(2*3),exp(2*4)])
        >>> log(c(0))
        -2.0
        >>> log(c(1))
        2.0
        >>> log(c(1.5))
        4.0
        >>> log(c(1.51))
        4.04
        >>> log(c(2))
        6.0
        >>> log(c(4))
        10.0

        .. note::

            **loglinear** requires strictly positive values $0<y_1 \dots y_n$.

        """
        if not all(0. < y for y in y_list):
            raise ValueError(
                'log interpolation requires positive values. Got %s' % str(
                    y_list))
        z = [x for x in x_list if not x]
        self._y_at_zero = y_list[x_list.index(z[0])] if z else None
        log_y_list = [log(y) / x for x, y in zip(x_list, y_list) if x]
        x_list = [x for x in x_list if x]
        super(loglinearrate, self).__init__(x_list, log_y_list)

    def __call__(self, x):
        if not x:
            return self._y_at_zero
        log_y = super(loglinearrate, self).__call__(x)
        return exp(log_y * x)


class logconstantrate(constant):
    def __init__(self, x_list=(), y_list=()):
        r""" log-constant interpolation by annual rates

        :param x_list: points $x_1 \dots x_n$
        :param y_list: values $y_1 \dots y_n$

        A |logconstantrate()| object is a function $f$
        returning at $x$ the float $\exp(x \cdot y)$
        of the constant interpolated float $y$ of
        $\log(\frac{y_i}{x_i})$
        when $x_i \leq x < x_{i+1}$, i.e.
        $$f(x)=\exp\Big(x \cdot \log(\frac{y_i}{x_i})\Big)$$

        >>> from math import log, exp
        >>> from yieldcurves.interpolation import logconstantrate
        >>> c = logconstantrate([1,2,3], [exp(1*2),exp(2*3),exp(2*4)])
        >>> log(c(1))
        2.0
        >>> log(c(1.5))
        3.0
        >>> log(c(1.51))
        3.02
        >>> log(c(2))
        6.0
        >>> log(c(3))
        8.0

        .. note::

            **logconstantrate** requires strictly positive values $0<y_1 \dots y_n$.

        """  # noqa 501
        if not all(0. < y for y in y_list):
            raise ValueError('log interpolation requires positive values.')
        z = [x for x in x_list if not x]
        self._y_at_zero = y_list[x_list.index(z[0])] if z else None
        log_y_list = [-log(y) / x for x, y in zip(x_list, y_list) if x]
        x_list = [x for x in x_list if x]
        super(logconstantrate, self).__init__(x_list, log_y_list)

    def __call__(self, x):
        if not x:
            return self._y_at_zero
        log_y = super(logconstantrate, self).__call__(x)
        return exp(-log_y * x)


@prettyclass
class base_extrapolation:

    def __init__(self, mid, left=None, right=None):
        self.mid = mid
        self.left = left
        self.right = right

        domain = self.mid.x_list
        self.min_max_x = min(domain), max(domain)

    def __call__(self, x):
        min_x, max_x = self.min_max_x

        if isinstance(x, (int, float)):
            if self.left and x < min_x:
                return self.left(x)
            if self.right and max_x < x:
                return self.right(x)
            return self.mid(x)

        # interpolation
        y = self.mid(_ for _ in x if min_x <= x <= max_x)

        # left extrapolation
        if self.left:
            y = self.left(_ for _ in x if x < min_x) + y

        # right extrapolation
        if self.right:
            y = y + self.right(_ for _ in x if max_x < x)

        return y


class extrapolation(base_extrapolation):

    def __init__(self, x_list, y_list, mid=linear, left=None, right=None):
        m_ = mid(x_list, y_list)
        l_ = left(x_list, y_list)
        r_ = right(x_list, y_list)
        super(extrapolation, self).__init__(m_, l_, r_)


class waterfall_extrapolation(base_extrapolation):

    def __init__(self, mid, *higher, left=None, right=None):
        if len(higher):
            left = waterfall_extrapolation(*higher, left=left)
        super(waterfall_extrapolation, self).__init__(mid, left, right)
