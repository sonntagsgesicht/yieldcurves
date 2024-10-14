# -*- coding: utf-8 -*-

# yieldcurves
# -----------
# A Python library for financial yield curves.
#
# Author:   sonntagsgesicht
# Version:  0.2.6.1, copyright Monday, 14 October 2024
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


from warnings import warn

try:
    from numpy import array as Matrix, eye as Identity  # noqa F401
except ImportError:
    def Matrix(*_, **__):
        msg = ("multi factor models require 'numpy', "
               "consider 'pip install numpy'.")
        warn(msg)

    def Identity(*_, **__):
        msg = ("multi factor models require 'numpy', "
               "consider 'pip install numpy'.")
        warn(msg)


def cholesky(A, lower=True):
    """
    Performs the Cholesky decomposition of a matrix A.
    A must be a symmetric, positive-definite matrix.

    Returns the lower triangular matrix L such that A = L * L.T
    """
    import numpy as np

    A = Matrix(A)
    n = A.shape[0]
    L = A * 0

    for i in range(n):
        for j in range(i + 1):
            if i == j:  # Diagonal elements
                sum_k = np.sum(L[i, :j] ** 2)
                L[i, j] = np.sqrt(A[i, i] - sum_k)
            else:  # Off-diagonal elements
                sum_k = np.sum(L[i, :j] * L[j, :j])
                L[i, j] = (A[i, j] - sum_k) / L[j, j]

    return L if lower else L.T
