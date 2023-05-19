from .repr import representation


class CallWrapper:
    """wrapper to set instance method as callable feature

    let :code:`curve.foo` be a method
    then use :code:`foo = CallableWrapper.new('foo')`
    as :code:`foo(curve)(x)`
    for :code:`curve.foo(x)`

    """
    __slots__ = 'curve', 'func'

    def __init__(self, curve, func=None):
        self.curve = curve
        self.func = func or self.__class__.__name__

    def __str__(self):
        return representation(self, self.curve, rstyle=False)

    def __repr__(self):
        return representation(self, self.curve)

    def __getattr__(self, item):
        return getattr(self.curve, item)

    def __getitem__(self, item):
        return self.curve[item]

    def __setitem__(self, key, value):
        self.curve[key] = value

    def __delitem__(self, key):
        del self.curve[key]

    def __call__(self, *x):
        return getattr(self.curve, self.func)(*x)

    @classmethod
    def new(cls, *names):
        """generate multiple CallableWrapper subtypes by names"""
        return tuple(type(name, (cls,), {}) for name in names)


price, yields = CallWrapper.new('price', 'yields')
prob, pd, marginal = CallWrapper.new('prob', 'pd', 'marginal')
intensity, hazard_rate = CallWrapper.new('intensity', 'hazard_rate')
df, rate, cash, short = CallWrapper.new('df', 'rate', 'cash', 'short')
vol, instantaneous = CallWrapper.new('vol', 'instantaneous')
