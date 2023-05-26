
from reprlib import Repr

_repr = Repr()
_repr.maxlist = _repr.maxtuple = 2
_repr.maxset = _repr.maxfrozenset = 2
_repr.maxdict = 5
_repr.maxsting = _repr.maxother = 80


def representation(obj, *args, rstyle=True, **kwargs):
    name = obj.__class__.__qualname__
    r = repr if rstyle else _repr.repr
    inner = list(map(r, args))
    inner += [str(k) + '=' + r(v)
              for k, v in kwargs.items() if v is not None]
    return name + '(' + ', '.join(inner) + ')'


def slots(x, *args, protected=False):
    """function returns attributes as set in `__slots__`

    attributes are split into argument tuple and keyword mapping
    where the argument tuple is build of `*args` arguments.
    """
    _kwargs = dict((k, getattr(x, k)) for k in x.__slots__ or ())
    # _kwargs.update(getattr(x, '__dict__', {}))
    if not protected:
        _kwargs = dict((k, v) for k, v in _kwargs if not k.startswith('_'))
    _args = [_kwargs.pop(i) for i in args if i in _kwargs]
    return _args, _kwargs


def attr(x, *args, protected=False):
    """function returns attributes of an object

    attributes are split into argument tuple and keyword mapping
    where the argument tuple is build of `*args` arguments.

    if `protected` is **True** also attributes starting with an underscore
    are returned.
    """
    _kwargs = dict((k, getattr(x, k)) for k in x.__slots__ or ())
    _kwargs.update(getattr(x, '__dict__', {}))
    if not protected:
        _kwargs = dict((k, v) for k, v in _kwargs if not k.startswith('_'))
    _args = [_kwargs.pop(i) for i in args if i in _kwargs]
    return _args, _kwargs


def repr_attr(x, *args, rstyle=True):
    _args, _kwargs = attr(x, *args)
    return representation(x, *_args, **_kwargs, rstyle=rstyle)


def repr_algebra(x, m=(), d=(), a=(), s=(), rstyle=True):
    # return x * m*...*m / d/.../d + a+...+a - s-...-s
    r = repr if rstyle else str
    x = r(x)
    x += ' * ' + ' * '.join(map(r, m)) if m else ''
    x += ' / ' + ' / '.join(map(r, d)) if d else ''
    x += ' + ' + ' + '.join(map(r, a)) if a else ''
    x += ' - ' + ' - '.join(map(r, s)) if s else ''
    return x
