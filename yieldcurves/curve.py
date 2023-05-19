from math import prod


# --- base curve classes ---


class ghost_curve:
    __slots__ = 'value',

    def __init__(self, value=0.0):
        self.value = value

    def __repr__(self):
        return str(self.value)

    def __float__(self):
        return float(self.value)

    def __bool__(self):
        return bool(self.value)

    def __eq__(self, other):
        return float(other) == float(self)

    def __call__(self, x=0.0):
        return self.value

    def __iter__(self):
        return iter([])


def init_curve(curve):
    return ghost_curve(curve) if isinstance(curve, (int, float)) else curve


class curve_algebra:
    """algebraic operations on curves

    (c1 + ... + cn)
    * m1 * ... * mk / d1 / ... / dl
    + a1 + ... at - s1 - ... - sr"""
    __slots__ = 'curves', 'add', 'sub', 'mul', 'div', '_inplace', 'spread', 'leverage'

    def __init__(self, *curves, add=(), sub=(), mul=(), div=(), inplace=False):
        self._inplace = inplace
        self.spread = 0.0
        self.leverage = 1.0
        self.curves = [init_curve(curve) for curve in curves]
        self.add = [init_curve(curve) for curve in add]
        self.sub = [init_curve(curve) for curve in sub]
        self.mul = [init_curve(curve) for curve in mul]
        self.div = [init_curve(curve) for curve in div]

        if len(curves) == 1 and isinstance(curves[0], curve_algebra):
            other = curves[0]
            self.spread = other.spread
            self.leverage = other.leverage
            self.curves = other.curves
            self.add.extend(other.add)
            self.sub.extend(other.sub)
            self.mul.extend(other.mul)
            self.div.extend(other.div)

    def __copy__(self):
        return curve_algebra(*self.curves, add=self.add, sub=self.sub,
                             mul=self.mul, div=self.div, inplace=self._inplace)

    def __iter__(self):
        return sorted(set().union(*self.curves))

    def __contains__(self, item):
        return item in self.curves

    def __call__(self, x):
        r = sum(c(x) for c in self.curves)
        r *= prod(m(x) for m in self.mul)
        r /= prod(d(x) for d in self.div)
        r += sum(a(x) for a in self.add)
        r -= sum(s(x) for s in self.sub)
        return self.spread + self.leverage * r

    def __add__(self, other):
        curve = self if self._inplace else self.__copy__()
        other = init_curve(other)
        if other in curve.sub:
            curve.sub.pop(curve.sub.index(other))
        else:
            curve.add.append(other)
        return curve

    def __sub__(self, other):
        curve = self if self._inplace else self.__copy__()
        other = init_curve(other)
        if other in curve.add:
            curve.add.pop(curve.add.index(other))
        else:
            curve.sub.append(other)
        return curve

    def __mul__(self, other):
        curve = self if self._inplace else self.__copy__()
        other = init_curve(other)
        if other in curve.div:
            curve.div.pop(curve.div.index(other))
        else:
            curve.mul.append(other)
        return curve

    def __truediv__(self, other):
        curve = self if self._inplace else self.__copy__()
        other = init_curve(other)
        if other in curve.mul:
            curve.mul.pop(curve.mul.index(other))
        else:
            curve.div.append(other)
        return curve

    def __repr__(self):
        str_repr = str
        r = '( ' + ' + '.join(map(str_repr, self.curves)) + ' )'
        r += ' + ' + ' + '.join(map(str_repr, self.add))
        r += ' - ' + ' - '.join(map(str_repr, self.sub))
        r += ' * ' + ' * '.join(map(str_repr, self.mul))
        r += ' / ' + ' / '.join(map(str_repr, self.div))
        return r
