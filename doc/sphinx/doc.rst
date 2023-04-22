
.. py:module:: yieldcurves

-----------------
API Documentation
-----------------

.. toctree::

Curve Objects
=============

Basic Curves
------------

.. module:: yieldcurves.curve

.. autosummary::
    :nosignatures:

    Price
    Curve
    DateCurve
    ForwardCurve
    RateCurve

.. inheritance-diagram:: yieldcurves.curve
    :top-classes: yieldcurves.curve.Curve
    :parts: 1

.. autoclass:: Price
.. autoclass:: Curve
.. autoclass:: DateCurve
.. autoclass:: ForwardCurve
.. autoclass:: RateCurve

.. autofunction:: rate_table


Interest Rate Curves
--------------------

.. module:: yieldcurves.interestratecurve

.. autosummary::
    :nosignatures:

    InterestRateCurve
    ZeroRateCurve
    DiscountFactorCurve
    CashRateCurve
    ShortRateCurve

.. inheritance-diagram:: yieldcurves.interestratecurve
    :parts: 1
    :top-classes: yieldcurves.curve.RateCurve

.. autoclass:: InterestRateCurve
.. autoclass:: ZeroRateCurve
.. autoclass:: DiscountFactorCurve
.. autoclass:: CashRateCurve
.. autoclass:: ShortRateCurve


Credit Curves
-------------

.. module:: yieldcurves.creditcurve

.. autosummary::
    :nosignatures:

    CreditCurve
    SurvivalProbabilityCurve
    FlatIntensityCurve
    HazardRateCurve
    MarginalSurvivalProbabilityCurve
    MarginalDefaultProbabilityCurve

.. inheritance-diagram:: yieldcurves.creditcurve
    :parts: 1
    :top-classes: yieldcurves.curve.RateCurve

.. autoclass:: CreditCurve
.. autoclass:: ProbabilityCurve
.. autoclass:: SurvivalProbabilityCurve
.. autoclass:: DefaultProbabilityCurve
.. autoclass:: FlatIntensityCurve
.. autoclass:: HazardRateCurve
.. autoclass:: MarginalSurvivalProbabilityCurve
.. autoclass:: MarginalDefaultProbabilityCurve


Fx Curve
--------

.. module:: yieldcurves.fx

.. autosummary::
    :nosignatures:

    FxForwardCurve

.. inheritance-diagram:: yieldcurves.fx.FxForwardCurve
    :parts: 1
    :top-classes: yieldcurves.curve.DateCurve

.. autoclass:: FxRate
    :inherited-members:

.. autoclass:: FxForwardCurve

Fundamentals
============

Interpolation
-------------

.. automodule:: yieldcurves.interpolation


Compounding
-----------

.. automodule:: yieldcurves.compounding


DayCount
--------

.. automodule:: yieldcurves.daycount
