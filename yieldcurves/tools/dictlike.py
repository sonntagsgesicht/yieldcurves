# -*- coding: utf-8 -*-

# yieldcurves
# -----------
# A Python library for financial yield curves.
#
# Author:   sonntagsgesicht
# Version:  0.1, copyright Saturday, 22 April 2023
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


class DictLike:

    curve = {}

    @staticmethod
    def _func(x):
        return x + 2

    @staticmethod
    def _inv(x):
        return x - 2

    def __getattr__(self, item):
        if hasattr(self.curve, item):
            def func(*args, **kwargs):
                args = tuple(self._func(x) for x in args)
                kwargs = {x: self._func(y) for x, y in kwargs.items()}
                return getattr(self.curve, item)(*args, **kwargs)
            func.__qualname__ = self.__class__.__qualname__ + '.' + item
            func.__name__ = item
            return func
        msg = f"{self.__class__.__name__!r} object has no attribute {item!r}"
        raise AttributeError(msg)

    def __getitem__(self, item):
        return self.curve.__getitem__(self._func(item))

    def __setitem__(self, key, value):
        self.curve.__setitem__(self._func(key), value)

    def __delitem__(self, key):
        self.curve.__delitem__(self._func(key))

    def __iter__(self):
        return iter(map(self._inv, self.curve.__iter__()))

    def __len__(self):
        return self.curve.__len__()

    def __contains__(self, item):
        return self.curve.__contains__(self._func(item))

    def update(self, other):
        self.curve.update({self._func(x): y for x, y in other.items()})


if __name__ == '__main__':

    d = DictLike()
    d.update({x: x for x in range(3)})
    for x in d.__iter__():
        print(x)
    print(d.curve, str(d.keys))


''' # YieldCurve

    def __getitem__(self, item):
        return self.curve[item]

    def __setitem__(self, key, value):
        self.curve[key] = value

    def __delitem__(self, key):
        del self.curve[key]

    def __iter__(self):
        return iter(self.curve)

    def __len__(self):
        if hasattr(self.curve, '__len__'):
            return len(self.curve)
        raise AttributeError

    def __contains__(self, item):
        if hasattr(self.curve, '__contains__'):
            return item in self.curve

'''
