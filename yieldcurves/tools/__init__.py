from scipy.integrate import quad as _integrate  # noqa F401

EPS = 1 / 250


# integrate = (lambda c, x, y: _integrate(c, float(x), float(y)))
integrate = _integrate
