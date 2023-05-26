from math import prod

from .repr import attr, repr_attr, repr_algebra

from . import daycount as _day_count
from . import interpolation as _interpolation


# --- base curve classes ---


class curve_wrapper:
    """wrapper to set instance method as callable feature

    let :code:`curve.foo` be a method
    then use :code:`foo = CallableWrapper.new('foo')`
    as :code:`foo(curve)(x)`
    for :code:`curve.foo(x)`

    """

    def __init__(self, curve, **__):
        self.curve = curve
        for k, v in __:
            setattr(self, k, v)

    def __copy__(self):
        args, kwargs = attr(self, 'curve')
        return self.__class__(*args, **kwargs)

    def __str__(self):
        return repr_attr(self, 'curve', rstyle=False)

    def __repr__(self):
        return repr_attr(self, 'curve')

    def __bool__(self):
        return bool(self.curve)

    def __getattr__(self, item):
        return getattr(self.curve, item)

    def __getitem__(self, item):
        return self.curve[item]

    def __setitem__(self, key, value):
        self.curve[key] = value

    def __delitem__(self, key):
        del self.curve[key]

    def __iter__(self):
        return iter(self.curve)

    def __contains__(self, item):
        return item in self.curve

    def __call__(self, *x):
        return self.curve(*x)


class call_wrapper(curve_wrapper):
    """wrapper to set instance method as callable feature

    let :code:`curve.foo` be a method
    then use :code:`foo = CallableWrapper.new('foo')`
    as :code:`foo(curve)(x)`
    for :code:`curve.foo(x)`

    """

    def __init__(self, curve, *, func=None, **__):
        func = func or self.__class__.__name__
        super().__init__(curve, func=func, **__)

    def __call__(self, *x):
        if callable(self.func):
            return self.func(self.curve, *x)
        return getattr(self.curve, self.func)(*x)


def generate_call_wrapper(*names, **names_funcs):
    """generate multiple call_wrapper subtypes by names"""
    r = tuple(type(n, (call_wrapper,), {}) for n in names)
    nf = names_funcs.items()
    r += tuple(type(n, (call_wrapper,), {'func': f}) for n, f in nf)
    return r


class invisible_curve_wrapper(curve_wrapper):

    def __copy__(self):
        return self.curve.__copy__()

    def __str__(self):
        return str(self.curve)

    def __repr__(self):
        return repr(self.curve)


def interpolation_builder(x_list, y_list, interpolation):
    # gather interpolation
    if isinstance(interpolation, str):
        i_type = getattr(_interpolation, interpolation)
    else:
        i_type = interpolation
        interpolation = getattr(i_type, '__name__', str(i_type))
    return invisible_curve_wrapper(i_type(x_list, y_list),
                                   interpolation=interpolation)


class typed_wrapper(invisible_curve_wrapper):

    def __init__(self, curve, curve_type=None, args=(),  **kwargs):
        if curve_type:
            curve = curve_type(curve, *args)
        super().__init__(curve, curve_type=curve_type, args=args, **kwargs)


class float_curve(invisible_curve_wrapper):

    def __init__(self, curve=0.0):
        super().__init__(curve)

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

    def __call__(self, *x):
        return self.curve

    def __iter__(self):
        return iter([])

    def __contains__(self, item):
        return item == self


def init_curve(curve):
    if isinstance(curve, (int, float)):
        return float_curve(curve)
    if isinstance(curve, curve_wrapper):
        return curve
    else:
        return invisible_curve_wrapper(curve)


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

    def __call__(self, x):
        r = self.curve(x)
        r *= prod(m(x) for m in self.mul)
        r /= prod(d(x) for d in self.div)
        r += sum(a(x) for a in self.add)
        r -= sum(s(x) for s in self.sub)
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




class DateCurve(curve_wrapper):

    date_type = None

    def __init__(self, curve, origin=None, day_count=None, **kwargs):
        """
        :param curve: underlying curve
        :param day_count: function to calculate year fractions
            (time between dates as a float)
        :param origin: origin date of curve
        :param curve_type:
        :param **kwargs:
        """

        # build curve
        if isinstance(curve, DateCurve):
            day_count = day_count or curve.day_count
            origin = origin or curve.origin
            curve = curve.curve

        # gather origin
        if origin is None:
            date_type = self.__class__.date_type
            if date_type is None:
                origin = 0.0
            elif hasattr(date_type, 'today'):
                origin = date_type.today()
            else:
                origin = date_type()

        curve = init_curve(curve)
        super().__init__(curve, origin=origin, day_count=day_count, **kwargs)

    def __getattr__(self, item):
        attr = getattr(self.curve, item)
        if callable(attr):
            return lambda *a, **kw: attr(*self._yf(a), **self._yf(kw))
        return attr

    def __iter__(self):
        # inverse of day_count(origin, x) -> origin + yf
        return iter(self.origin + yf for yf in self.curve)

    def __contains__(self, item):
        return self._yf(item) in self.curve

    def __call__(self, x, *args, **kwargs):
        return self.curve(self._yf(x), *self._yf(args), **self._yf(kwargs))

    def _yf(self, x):
        if not x:
            return x
        origin = self.origin
        day_count = self.day_count or _day_count
        if isinstance(x, (list, tuple)):
            return type(x)([day_count(origin, a) for a in x])
        if isinstance(x, dict):
            y, *_ = x.values()
            return dict((k, day_count(origin, v)) for k, v in x.items())
        return day_count(origin, x)


class ParametricDateCurve(DateCurve):

    def __init__(self, function, param=None, origin=None, day_count=None,
                 **kwargs):

        # build curve
        if param is None:
            # if no param given + function is curve_wrapper bypass curve build
            if isinstance(function, curve_wrapper):
                f_curve = function
            else:
                f_curve = function()
        elif isinstance(param, (list, tuple)):
            f_curve = function(*param)
        elif isinstance(param, dict):
            f_curve = function(**param)
        else:
            f_curve = function(param)

        super().__init__(f_curve, origin=origin, day_count=day_count, **kwargs)


class InterpolatedDateCurve(DateCurve):

    interpolation_type = None

    def __init__(self, domain, data=None, interpolation=None, origin=None,
                 day_count=None, **kwargs):

        # build curve
        if data is None:
            # if no data given bypass i_type build
            curve, domain = domain, ()
        else:
            cls = type(domain)
            yf_domain = cls(self._yf(d) for d in domain)
            if interpolation is None:
                interpolation = self.__class__.interpolation_type
            curve = interpolation_builder(yf_domain, data, interpolation)

        super().__init__(curve, domain=domain, data=data,
                         interpolation=curve.interpolation,
                         origin=origin, day_count=day_count, **kwargs)

    def __iter__(self):
        if isinstance(self.domain, (int, float)):
            return iter([])
        return iter(self.domain)
