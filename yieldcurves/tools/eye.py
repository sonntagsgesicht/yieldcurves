
from .pp import pretty


@pretty
class eye:
    def __init__(self, curve=None):
        r"""identity function $x \mapsto x$

        :param x: float
        :return: identity value **x**
        """
        self.curve = curve

    def __call__(self, x):
        return x if self.curve is None else self.curve(x)
