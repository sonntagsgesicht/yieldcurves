def trapezoidal_rule(f, a, b, n):
    """
    Numerically integrate the function f from a to b using the trapezoidal rule with n intervals.

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


    # Define the function to integrate
    def func(x):
        return math.sin(x)


    # Integrate func from 0 to π with 1000 intervals
    result = trapezoidal_rule(func, 0, math.pi, 1000)
    print("Integral result:", result)
