# -*- coding: utf-8 -*-

# yieldcurves
# -----------
# A Python library for financial yield curves.
#
# Author:   sonntagsgesicht
# Version:  0.1, copyright Thursday, 12 April 2023
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


from bisect import bisect_left, bisect_right
from collections import UserDict
from math import exp, log

from .tools.repr import representation


class _base_interpolation(object):
    """
    Basic class to interpolate given data.
    """

    def __init__(self, x_list=(), y_list=()):
        r""" interpolation class

        :param x_list: points $x_1 \dots x_n$
        :param y_list: values $y_1 \dots y_n$

        """
        self.x_list = list()
        self.y_list = list()
        self._update(x_list, y_list)

    def __call__(self, x):
        raise NotImplementedError

    def __contains__(self, item):
        return item in self.x_list

    def _update(self, x_list=(), y_list=()):
        """ _update interpolation data
        :param list(float) x_list: x values
        :param list(float) y_list: y values
        """
        if not y_list:
            for x in x_list:
                if x in self.x_list:
                    i = self.x_list.index(float(x))
                    self.x_list.pop(i)
                    self.y_list.pop(i)
        else:
            x_list = list(map(float, x_list))
            y_list = list(map(float, y_list))
            data = [(x, y) for x, y in
                    zip(self.x_list, self.y_list) if x not in x_list]
            data.extend(list(zip(x_list, y_list)))
            data = sorted(data)
            self.x_list = [float(x) for (x, y) in data]
            self.y_list = [float(y) for (x, y) in data]

    @classmethod
    def from_dict(cls, xy_dict):
        r"""create an interpolation instance object from **dict**

        :param xy_dict: dictionary with sorted keys serving as **x_list**
            and values as **y_list**
        :return: interpolation object
        """

        return cls(sorted(xy_dict), (xy_dict[k] for k in sorted(xy_dict)))


class base_interpolation(UserDict):
    """
    Basic class to interpolate given data.
    """

    @property
    def x_list(self):
        return list(self.keys())

    @property
    def y_list(self):
        return list(self.values())

    def __init__(self, x_list=(), y_list=()):
        r""" interpolation class

        :param x_list: points $x_1 \dots x_n$
        :param y_list: values $y_1 \dots y_n$

        """
        # new implementation since dicts are ordered in Python 3.8
        if not len(set(x_list)) == len(x_list):
            raise KeyError(f"identical x values in {x_list}")
        # super().__init__(sorted(zip(x_list, y_list)))
        super().__init__(zip(map(float, x_list), map(float, y_list)))

    def __call__(self, x):
        return float(x)

    def __setitem__(self, key, value):
        super().__setitem__(float(key), float(value))
        self.data = dict(sorted(self.data.items()))

    def __str__(self):
        return representation(self, self.x_list, self.y_list, rstyle=False)

    def __repr__(self):
        return representation(self, self.x_list, self.y_list)

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


class default_value_interpolation(base_interpolation):
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

        >>> from yieldcurves.interpolation import default_value_interpolation
        >>> # c = default_value_interpolation([1,2,3,1], [1,2,3,4], default_value=42)
        >>> c = default_value_interpolation([1,2,3], [1,2,3], default_value=42)
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

    def __str__(self):
        return representation(self, self.x_list, self.y_list,
                              default_value=self._default, rstyle=False)

    def __repr__(self):
        return representation(self, self.x_list, self.y_list,
                              default_value=self._default)


class no(default_value_interpolation):
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


class zero(default_value_interpolation):
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

    def __str__(self):
        return representation(self, self.mid, left=self.left, right=self.right,
                              rstyle=False)

    def __repr__(self):
        return representation(self, self.mid, left=self.left, right=self.right)


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


class interpolation_scheme(object):
    _interpolation = constant, linear, constant

    def __init__(self, domain, data, interpolation=None):
        r"""class to build piecewise interpolation function

        :param list(float) domain: points $x_1 \dots x_n$
        :param list(float) data: values $y_1 \dots y_n$
        :param function interpolation:
            interpolation function on **x_list** (optional)
            or triple of (**left**, **mid**, **right**)
            interpolation functions with

            * **left** for $x < x_1$ (as default **right** is used)
            * **mid** for $x_1 \leq x \leq x_n$ (as default |linear| is used)
            * **right** for $x > x_n$ (as default |constant| is used)

        Curve object to build function
        $$f(x) = y$$
        using piecewise various interpolation functions.
        """

        if not interpolation:
            interpolation = self.__class__._interpolation

        y_left, y_mid, y_right = self.__class__._interpolation
        if isinstance(interpolation, (tuple, list)):
            if len(interpolation) == 3:
                y_left, y_mid, y_right = interpolation
            elif len(interpolation) == 2:
                y_mid, y_right = interpolation
                y_left = y_right
            elif len(interpolation) == 1:
                y_mid, = interpolation
            else:
                raise ValueError
        elif issubclass(interpolation, base_interpolation):
            y_mid = interpolation
        else:
            raise AttributeError

        if not len(domain) == len(data):
            raise AssertionError()
        if not len(domain) == len(set(domain)):
            raise AssertionError()

        #: Interpolation:
        self._y_mid = y_mid(domain, data)
        self._y_right = y_right(domain, data)
        self._y_left = y_left(domain, data)

    def __call__(self, x):
        y = 0.0
        if x < self._y_left.x_list[0]:
            # extrapolate to left
            y = self._y_left(x)
        elif x > self._y_right.x_list[-1]:
            # extrapolate to right
            y = self._y_right(x)
        else:
            # interpolate in the middle
            y = self._y_mid(x)
        return y


def _dyn_scheme(left, mid, right):
    name = left.__name__ + '_' + mid.__name__ + '_' + right.__name__
    return type(name, (interpolation_scheme,),
                {'_interpolation': (left, mid, right)})


constant_linear_constant = _dyn_scheme(constant, linear, constant)
linear_scheme = constant_linear_constant

logconstant_loglinear_logconstant = _dyn_scheme(constant, loglinear, constant)
log_linear_scheme = logconstant_loglinear_logconstant

logconstantrate_loglinearrate_logconstantrate = _dyn_scheme(
    logconstantrate, loglinearrate, logconstantrate)
log_linear_rate_scheme = logconstantrate_loglinearrate_logconstantrate

zero_linear_constant = _dyn_scheme(zero, linear, constant)
zero_linear_scheme = zero_linear_constant
