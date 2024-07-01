
.. currentmodule:: yieldcurves

To start with import the package.

.. doctest::

    >>> from yieldcurves import YieldCurve, DateCurve


Yield Curve Objects
===================

Yield curves can be expressed in various ways.
Each for different type of storing rate information and purpose.

There are three different types of usage of yield curves:

    asset yield curve, interest rate curve and credit curves.

They meet all the same input, a continuous compounded yield curve,
either as yield or spot rate curve, zero rate curve or intensity curve.

Their usage differs only in derived output like futur prices or
discount factors or probabilities of default.

On the other hand yield curves can be constructed form those data, too.

The purpose of |YieldCurve| is to provide construction routines and
calculation methods for all of those.
