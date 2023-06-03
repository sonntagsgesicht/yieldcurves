
from scipy.optimize import leastsq

from lmfit import minimize, create_params


curve = {}
curve.__call__ = lambda x: x
x = y = 0


def err(p, x, y):
    curve.update(p)
    return curve(x) - y


_ = leastsq(err, curve[curve], args=(x, y))

# create_params(beta0={'value': 0.007, 'min': 0, 'max': 1})
_ = minimize(err, create_params(**curve), args=(x, y)).params
