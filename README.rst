
Python library *yieldcurves*
----------------------------

.. image:: https://github.com/sonntagsgesicht/yieldcurves/actions/workflows/python-package.yml/badge.svg
    :target: https://github.com/sonntagsgesicht/yieldcurves/actions/workflows/python-package.yml
    :alt: GitHubWorkflow

.. image:: https://img.shields.io/readthedocs/yieldcurves
   :target: http://yieldcurves.readthedocs.io
   :alt: Read the Docs

.. image:: https://img.shields.io/github/license/sonntagsgesicht/yieldcurves
   :target: https://github.com/sonntagsgesicht/yieldcurves/raw/master/LICENSE
   :alt: GitHub

.. image:: https://img.shields.io/github/release/sonntagsgesicht/yieldcurves?label=github
   :target: https://github.com/sonntagsgesicht/yieldcurves/releases
   :alt: GitHub release

.. image:: https://img.shields.io/pypi/v/yieldcurves
   :target: https://pypi.org/project/yieldcurves/
   :alt: PyPI Version

.. image:: https://img.shields.io/pypi/pyversions/yieldcurves
   :target: https://pypi.org/project/yieldcurves/
   :alt: PyPI - Python Version

.. image:: https://pepy.tech/badge/yieldcurves
   :target: https://pypi.org/project/yieldcurves/
   :alt: PyPI Downloads

A Python library for financial yield curves.
Typical banking business methods are provided like interpolation, compounding,
discounting and fx.


Example Usage
-------------


>>> from yieldcurves import YieldCurve
>>> from yieldcurves.interpolation import linear

>>> time_grid = [0, 2]
>>> rate_grid = [.03, .05]
>>> curve = linear(time_grid, rate_grid)
>>> yc = YieldCurve(curve)
>>> yc.zero(0, 1)
0.040000000000000036

>>> yc.df(0, 1)
0.9607894391523232


Or use `datetime <https://docs.python.org/3/library/datetime.html>`_

>>> from yieldcurves import DateCurve
>>> from datetime import date

>>> start = date(2013, 1, 1)
>>> mid = date(2014, 1, 1)
>>> end = date(2015, 1, 1)


>>> dc = DateCurve.from_interpolation([start, end], [.03, .05], origin=start)
>>> dc.zero(start, mid)
0.03999999999999998

>>> dc.df(start, mid)
0.9608157444936446


The framework works fine with native `datetime <https://docs.python.org/3/library/datetime.html>`_
but we recommend `businessdate <https://pypi.org/project/businessdate/>`_ package
for more convenient functionality to roll out date schedules.



>>> from businessdate import BusinessDate, BusinessSchedule

So, build a date schedule.

>>> today = BusinessDate(20201031)
>>> schedule = BusinessSchedule(today, today + "8q", step="1q")
>>> schedule
[BusinessDate(20201031), BusinessDate(20210131), BusinessDate(20210430), BusinessDate(20210731), BusinessDate(20211031), BusinessDate(20220131), BusinessDate(20220430), BusinessDate(20220731), BusinessDate(20221031)]


Documentation
-------------

More documentation available at
`https://yieldcurves.readthedocs.io <https://yieldcurves.readthedocs.io>`_


Install
-------

The latest stable version can always be installed or updated via pip:

.. code-block:: bash

    $ pip install yieldcurves


Development Version
-------------------

The latest development version can be installed directly from GitHub:

.. code-block:: bash

    $ pip install --upgrade git+https://github.com/sonntagsgesicht/yieldcurves.git


Contributions
-------------

.. _issues: https://github.com/sonntagsgesicht/yieldcurves/issues
.. __: https://github.com/sonntagsgesicht/yieldcurves/pulls

Issues_ and `Pull Requests`__ are always welcome.


License
-------

.. __: https://github.com/sonntagsgesicht/yieldcurves/raw/master/LICENSE

Code and documentation are available according to the Apache Software License (see LICENSE__).


