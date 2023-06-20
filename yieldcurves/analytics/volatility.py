
from ..curve import CurveAdapter, init_curve


# inst vol -> terminal vol

class Terminal(CurveAdapter):
    """terminal vol from instantaneous vol curve"""

    def __init__(self, curve):
        super().__init__(init_curve(curve))

    def __call__(self, x, y=None):
        raise NotImplementedError()
