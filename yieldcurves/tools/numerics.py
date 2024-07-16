# -*- coding: utf-8 -*-

# yieldcurves
# -----------
# A Python library for financial yield curves.
#
# Author:   sonntagsgesicht
# Version:  0.2, copyright Monday, 01 July 2024
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


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


# Example usage:
if __name__ == "__main__":
    import math

    # Define the function to differentiate
    def func(x):
        return math.sin(x)

    # Differentiate func at x = π/4
    x_point = math.pi / 4
    derivative = finite_difference(func, x_point)
    print("Derivative at x =", x_point, "is", derivative)

    # Integrate func from 0 to π with 1000 intervals
    result = trapezoidal_rule(func, 0, math.pi, 1000)
    print("Integral result:", result)
