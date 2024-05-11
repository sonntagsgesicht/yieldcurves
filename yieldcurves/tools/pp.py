
from inspect import stack, signature


def prepr(self, *args, **kwargs):
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
        # use funcion name rather than repr string
        a = {k: getattr(v, '__qualname__', r(v)) for k, p, v in kpv if
             not v == p.default}
        b = s.bind(**a)
        if not is_str:
            pass
            # b.apply_defaults()
        args, kwargs = b.args, b.kwargs

    # build repr string
    params = tuple(f"{a}" for a in args) +\
             tuple(f"{k}={v}" for k, v in kwargs.items())
    return f"{self.__class__.__qualname__}({', '.join(params)})"
