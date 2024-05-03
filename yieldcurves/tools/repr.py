
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
    kwargs = {k: getattr(v, '__qualname__', r(v)) for k, v in kwargs.items() if v is not None}
    inner += [f"{k}={v}" for k, v in kwargs.items()]
    return name + '(' + ', '.join(inner) + ')'


def kwargs(x, protected=False, params=False):
    """function returns attributes of an object

    attributes are split into argument tuple and keyword mapping
    where the argument tuple is build of `*args` arguments.

    if `protected` is **True** also attributes starting with an underscore
    are returned.

    if `params` is **True** only attributes which are arguments of `__init__`
    are returned.
    """
    if hasattr(x, '__slots__'):
        _kwargs = {k: getattr(x, k) for k in x.__slots__ or ()}
    else:
        _kwargs = getattr(x, '__dict__', {})
    if not protected:
        _kwargs = {k: v for k, v in _kwargs.items() if not k.startswith('_')}
    if params:
        _ = [_kwargs[i] for i in signature(x.__class__).parameters
                   if i in _kwargs]
    return _kwargs


class ReprAdapter:

    def __str__(self):
        if hasattr(self, 'repr_str'):
            return getattr(self, 'repr_str')
        if hasattr(self, 'repr_repr'):
            return getattr(self, 'repr_repr')

        _kwargs = kwargs(self, params=True)
        if 'curve' in _kwargs:
            if getattr(self, 'repr_hidden', False):
                return str(getattr(self, 'curve'))
            curve = _kwargs.pop('curve', None)
            return representation(self, curve, **_kwargs, rstyle=False)
        return representation(self, **_kwargs, rstyle=False)

    def __repr__(self):
        if hasattr(self, 'repr_repr'):
            return getattr(self, 'repr_repr')

        _kwargs = kwargs(self, params=True)
        if 'curve' in _kwargs:
            if getattr(self, 'repr_hidden', False):
                return repr(getattr(self, 'curve'))
            curve = _kwargs.pop('curve', None)
            return representation(self, curve, **_kwargs, rstyle=True)
        return representation(self, **_kwargs, rstyle=True)
