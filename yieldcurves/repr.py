
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
