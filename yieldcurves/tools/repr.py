
from reprlib import Repr
from inspect import signature

_repr = Repr()
_repr.maxlist = _repr.maxtuple = 2
_repr.maxset = _repr.maxfrozenset = 2
_repr.maxdict = 5
_repr.maxsting = _repr.maxother = 80


def representation(obj, *args, rstyle=True, **kwargs):
    name = obj.__class__.__qualname__
    r = repr if rstyle else _repr.repr
    inner = list(getattr(a, '__qualname__', r(a)) for a in args)
    kwargs = {k: getattr(v, '__qualname__', r(v)) for k, v in kwargs.items()}
    inner += [f"{k}={v}" for k, v in kwargs.items() if v]
    return name + '(' + ', '.join(inner) + ')'


def kwargs(x, protected=False):
    """function returns attributes of an object

    attributes are split into argument tuple and keyword mapping
    where the argument tuple is build of `*args` arguments.

    if `protected` is **True** also attributes starting with an underscore
    are returned.
    """
    if hasattr(x, '__slots__'):
        _kwargs = {k: getattr(x, k) for k in x.__slots__ or ()}
    else:
        _kwargs = getattr(x, '__dict__', {})
    if not protected:
        _kwargs = {k: v for k, v in _kwargs.items() if not k.startswith('_')}
    return _kwargs


def params(x, protected=False):
    _kwargs = kwargs(x, protected)
    _params = signature(x.__class__).parameters
    _ = [_kwargs.pop(i) for i in _kwargs if i not in _params]
    return _kwargs


def repr_attr(x, *args, rstyle=True):
    _kwargs = kwargs(x)
    _args = [_kwargs.pop(i) for i in args if i in _kwargs]
    return representation(x, *_args, **_kwargs, rstyle=rstyle)


class ReprAdapter:

    @property
    def __kwargs__(self):
        return params(self)

    def __copy__(self):
        _kwargs = self.__kwargs__
        curve = _kwargs.pop('curve')
        _kwargs['curve'] = getattr(curve, '__copy__', curve)
        return self.__class__(**_kwargs)

    def __str__(self):
        if getattr(self, 'hidden', False):
            return str(getattr(self, 'curve'))
        _kwargs = self.__kwargs__
        curve = _kwargs.pop('curve')
        return representation(self, curve, **_kwargs, rstyle=False)

    def __repr__(self):
        if getattr(self, 'hidden', False):
            return repr(getattr(self, 'curve'))
        _kwargs = self.__kwargs__
        curve = _kwargs.pop('curve')
        return representation(self, curve, **_kwargs, rstyle=True)
