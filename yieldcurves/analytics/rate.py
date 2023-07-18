
from ..compounding import compounding_factor, compounding_rate
from ..tools.adapter import CurveAdapter, init_curve


class CompoundingFactor(CurveAdapter):

    def __init__(self, curve, frequency=None, *, invisible=None):
        """discount factor curve from yield curve

        :param curve: yield curve
        :param frequency: compounding frequency
        :param invisible: hide adapter in string representation
        """
        super().__init__(init_curve(curve), invisible=invisible)
        self.frequency = frequency

    def __call__(self, x, y=None):
        if isinstance(self.curve, CompoundingFactor):
            return self.curve(x, y)
        if x == y:
            return 1.0
        if y is None:
            return compounding_factor(self.curve(x), x, self.frequency)
        if isinstance(self.curve, CompoundingRate):
            return compounding_factor(self.curve(x, y), y - x, self.frequency)
        fx = compounding_factor(self.curve(x), x, self.frequency)
        fy = compounding_factor(self.curve(y), y, self.frequency)
        return fy / fx


class CompoundingRate(CurveAdapter):

    def __init__(self, curve, frequency=None, *, invisible=None):
        """yield curve from discount factor curve

        :param curve: discount factor curve
        :param frequency: compounding frequency
        :param invisible: hide adapter in string representation

        hint to convert periodical compounded rates in to continuous rates

        >>> quarterly = CurveAdapter(.02)
        >>> f = CompoundingFactor(quarterly, frequency=4, invisible=True)
        >>> continuous = CompoundingRate(f, frequency=None, invisible=True)

        """
        super().__init__(init_curve(curve), invisible=invisible)
        self.frequency = frequency

    def __call__(self, x, y=None):
        if isinstance(self.curve, CompoundingFactor):
            return compounding_rate(self.curve(x, y), y - x, self.frequency)
        if y is None:
            return self.curve(x)
        fx = compounding_factor(self.curve(x), x, self.frequency)
        fy = compounding_factor(self.curve(y), y, self.frequency)
        return compounding_rate(fy / fx, y - x, self.frequency)
