def finite_difference(f, x, h=1e-7):
    """
    Numerically differentiate the function f at point x using the finite difference method.

    Parameters:
    f (function): The function to differentiate.
    x (float): The point at which to differentiate the function.
    h (float, optional): The step size to use. Default is 1e-7.

    Returns:
    float: The numerical derivative of f at point x.
    """
    return (f(x + h) - f(x - h)) / (2 * h)


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
