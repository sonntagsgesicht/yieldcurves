from typing import Callable, Union
from vectorizeit import vectorize

from .adapter import CallAdapter as _CurveAdapter, Curve, \
    init_curve  # noqa F401


class CurveAdapter(_CurveAdapter):

    def __init__(self,
                 curve: Curve,
                 *,
                 invisible: bool = None,
                 call: Union[str, Callable] = None,
                 pre: Callable = None,
                 inv: Callable = None):
        r"""Wrapper class for a curve (i.e. callable)

        :param curve: inner curve object $\phi: X \to Y$ to wrap around.
            This argument can be a single value $v$ which results in constant
            function $\phi(x)=v$.
        :param invisible: boolean flag to control string representation.
            If **True** both **str** and **repr** is forwarded to **curve**.
            (optional, default is **False** if **curve** is callable
            else **True**)
        :param call: name of method of to be invoked when wrapper is invoked
            via **__call__**
            (optional, default is **__call__**)
        :param pre: argument transformation function $\theta$
            performed prior **curve** is called,
            i.e. $\phi(\theta(x))$.
            (optional, default is $\theta(x) = id(x) = x$)
        :param inv: inverse $\theta^{-1}$  of argument transformation
            function $\theta$. $\theta^{-1}$ is performed to transform
            **curve** parameter arguments is called,
            i.e. $\theta^{-1}(\\theta(x)))$.
            (optional, default is $\theta^{-1}(x) = id(x) = x$)
        """
        super().__init__(curve, invisible=invisible, call=call)
        self.pre = pre
        self.inv = inv

        self._pre = pre or (lambda _: _)
        self._inv = pre or (lambda _: _)

    @vectorize()
    def __call__(self, *_, **__):
        _ = tuple(self._pre(x) for x in _)
        __ = dict((self._pre(x), v) for x, v in __.items())
        return super().__call__(*_, **__)

    def __getitem__(self, item):
        return super().__getitem__(self._pre(item))

    def __setitem__(self, key, value):
        return super().__setitem__(self._pre(key), value)

    def __delitem__(self, key):
        return super().__delitem__(self._pre(key))

    def __iter__(self):
        return iter(map(self._inv, super().__iter__()))

    def __contains__(self, item):
        return self._pre(item) in self.curve

    def keys(self):
        return iter(map(self._inv, super().keys()))

    def items(self):
        return dict((self._inv(k), v) for k, v in super().items()).items()

    def pop(self, item):
        return super().pop(self._pre(item))

    def update(self, data):
        data = dict((self._pre(k), v) for k, v in data.items())
        return super().update(data)

    def get(self, item, default=None):
        return super().get(self._pre(item), default)
