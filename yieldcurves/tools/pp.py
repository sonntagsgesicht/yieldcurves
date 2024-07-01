# -*- coding: utf-8 -*-

# yieldcurves
# -----------
# A Python library for financial yield curves.
#
# Author:   sonntagsgesicht
# Version:  0.1, copyright Saturday, 22 April 2023
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


from inspect import stack, signature


def prepr(self, *args, clsmethod='', sep=', ', **kwargs):
    # select repr function
    is_str = any(f.function == '__str__' for f in stack())
    r = str if is_str else repr

    # repr args
    args = [getattr(a, '__qualname__', r(a)) for a in args]
    kwargs = {k: getattr(v, '__qualname__', r(v)) for k, v in kwargs.items()}

    if not args and not kwargs:
        # scan attributes used as arguments
        s = signature(self.__class__)
        kpv = ((k, p, getattr(self, k, p.default)) for k, p in
               s.parameters.items())
        # use function name rather than repr string
        a = {k: getattr(v, '__qualname__', r(v)) for k, p, v in kpv if
             not v == p.default}
        b = s.bind(**a)
        if not is_str:
            pass
            # b.apply_defaults()
        args, kwargs = b.args, b.kwargs

    # build repr string
    params = tuple(f"{a}" for a in args) + \
        tuple(f"{k}={v}" for k, v in kwargs.items())
    clsmethod = '.' + clsmethod if clsmethod else ''
    return f"{self.__class__.__qualname__}{clsmethod}({sep.join(params)})"


class Pretty:

    def __init__(self, clsmethod='', sep=', ', args=(), kwargs=()):
        self.clsmethod = clsmethod
        self.sep = sep
        self.args = args
        self.kwargs = kwargs

    def __call__(self, obj, *args, clsmethod='', sep=', ', **kwargs):
        return prepr(obj, *args, clsmethod=clsmethod, sep=sep, **kwargs)


def pretty(cls):
    setattr(cls, '__str__', prepr)
    setattr(cls, '__repr__', prepr)
    return cls


def pp(clsmethod='', sep=', ', args=(), kwargs=()):
    return Pretty(clsmethod, sep, args, kwargs)
