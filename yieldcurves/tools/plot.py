# -*- coding: utf-8 -*-

# yieldcurves
# -----------
# A Python library for financial yield curves.
#
# Author:   sonntagsgesicht
# Version:  0.1, copyright Thursday, 12 April 2023
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


import matplotlib.pyplot as plt
import matplotlib

# matplotlib.use('WebAgg')
# matplotlib.use('TkAgg')
# matplotlib.use('QtCairo')
# matplotlib.use('QtAgg')
# matplotlib.use('module://backend_interagg')
matplotlib.use('MacOSX')


def plot(x, *curve, legend=True):
    fig, ax = plt.subplots(figsize=(10, 5))
    x = tuple(x)
    for c in curve:
        y = [c(_) for _ in x]
        ax.plot(x, y, label=str(c)[:50])
    ax.set_title('yield curve plot')
    ax.set_xlabel(r'time $t$')
    ax.set_ylabel(r'$x(t)$')
    if legend:
        ax.legend()
    plt.show()
