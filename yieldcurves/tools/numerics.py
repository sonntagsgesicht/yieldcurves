# -*- coding: utf-8 -*-

# yieldcurves
# -----------
# A Python library for financial yield curves.
#
# Author:   sonntagsgesicht
# Version:  0.2.1, copyright Tuesday, 16 July 2024
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


from scipy.integrate import quad  # noqa F401


def integrate(func, a, b):
    return quad(func, a, b)[0]


def finite_difference(f, x, h=1e-7):
    """
    Numerically differentiate the function f at point x
    using the finite difference method.

    Parameters:
    f (function): The function to differentiate.
    x (float): The point at which to differentiate the function.
    h (float, optional): The step size to use. Default is 1e-7.

    Returns:
    float: The numerical derivative of f at point x.
    """
    return (f(x + h) - f(x - h)) / (2 * h)


def trapezoidal_rule(f, a, b, n):
    """
    Numerically integrate the function f from a to b
    using the trapezoidal rule with n intervals.

    Parameters:
    f (function): The function to integrate.
    a (float): The start point of the interval.
    b (float): The end point of the interval.
    n (int): The number of intervals to divide [a, b] into.

    Returns:
    float: The numerical integral of f from a to b.
    """
    # Calculate the width of each interval
    h = (b - a) / n

    # Calculate the sum of f(x) for each interval
    integral = 0.5 * (f(a) + f(b))
    for i in range(1, n):
        integral += f(a + i * h)

    # Multiply by the width of the intervals
    integral *= h

    return integral


def quadrature(f, a, b):
    nodes = {0.0: 0.20948214108472782,
             -0.20778495500789848: 0.20443294007529889,
             0.20778495500789848: 0.20443294007529889,
             -0.4058451513773972: 0.19035057806478542,
             0.4058451513773972: 0.19035057806478542,
             -0.5860872354676911: 0.1690047266392679,
             0.5860872354676911: 0.1690047266392679,
             -0.7415311855993945: 0.14065325971552592,
             0.7415311855993945: 0.14065325971552592,
             -0.8648644233597691: 0.10479001032225019,
             0.8648644233597691: 0.10479001032225019,
             -0.9491079123427585: 0.06309209262997856,
             0.9491079123427585: 0.06309209262997856,
             -0.9914553711208126: 0.022935322010529224,
             0.9914553711208126: 0.022935322010529224}
    m = 0.5 * (b + a)
    h = 0.5 * (b - a)
    return sum(w * f(m + h * n) for n, w in nodes.items()) * h


# Example usage
if __name__ == "__main__":
    from math import exp, pi
    from scipy.integrate import quad as _scipy_quad

    f = (lambda x: exp(-x ** 2))
    a = 0.0
    b = 1.0
    n = 7

    print(f"quadrature:         {quadrature(f, a, b)}")
    print(f"scipy:              {_scipy_quad(f, a, b)[0]}")
    print(f"trapezoidal_rule:   {trapezoidal_rule(f, a, b, 1000)}")

# Example usage:
if __name__ == "__main__":

    # Differentiate func at x = π/4
    f = exp
    x_point = pi / 4
    a, b = -1, pi

    derivative = finite_difference(f, x_point)
    print("Derivative at x =", x_point, "is", derivative)

    # Integrate func from 0 to π with 1000 intervals
    result = trapezoidal_rule(f, a, b, 1000)
    print("Integral trapezoidal_rule result:", result)

    # Integrate func from 0 to π with 1000 intervals
    result = quadrature(f, a, b)
    print("Integral quadrature result:      ", result)

    # Integrate func from 0 to π with 1000 intervals
    result = _scipy_quad(f, a, b)[0]
    print("Integral scipy result:           ", result)
