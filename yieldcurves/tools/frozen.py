# -*- coding: utf-8 -*-

# yieldcurves
# -----------
# A Python library for financial yield curves.
#
# Author:   sonntagsgesicht
# Version:  0.2.1, copyright Tuesday, 16 July 2024
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


def frozen_attr(self, attr: str, value):
    print(f"set attribute {attr} on {self}")
    if hasattr(self, '_frozen') and not attr.startswith('_'):
        cls = self.__class__.__qualname__
        msg = f"Trying to set attribute {attr} on a frozen instance of {cls}"
        raise AttributeError(msg)
    return super().__setattr__(attr, value)


def frozen(cls):
    setattr(cls, '__setattr__', frozen_attr)
    return cls


class FrozenObject:

    def __setattr__(self, key, value):
        if hasattr(self, '_frozen') and not key.startswith('_'):
            cls = self.__class__.__qualname__
            msg = f"Trying to set attribute {key} " \
                  f"on a frozen instance of {cls}"
            raise AttributeError(msg)
        return super().__setattr__(key, value)

    def __init__(self):
        self._frozen = None
