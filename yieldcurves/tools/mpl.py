# -*- coding: utf-8 -*-

# yieldcurves
# -----------
# A Python library for financial yield curves.
#
# Author:   sonntagsgesicht
# Version:  0.1, copyright Saturday, 22 April 2023
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


from matplotlib import use, pyplot as plt

# import matplotlib
# matplotlib.use('WebAgg')
# matplotlib.use('TkAgg')
# matplotlib.use('QtCairo')
# matplotlib.use('QtAgg')
# matplotlib.use('module://backend_interagg')
# matplotlib.use('MacOSX')


def plot(x, *curve, legend=True, figsize=(10, 5), kind='plot', backend=None,
         params={}, show=True, xlim=(), ylim=(), **curves):
    if backend:
        use(backend)
    fig, ax = plt.subplots(figsize=figsize)
    plot = getattr(ax, kind)
    x = tuple(x)
    for c in curve:
        y = [c(_) for _ in x] if callable(c) else c
        plot(x, y, label=str(c)[:50], **params)
    for k in curves:
        c = curves[k]
        y = [c(_) for _ in x] if callable(c) else c
        plot(x, y, label=str(k)[:50], **params)
    ax.set_title('yield curve plot')
    ax.set_xlabel(r'time $t$')
    ax.set_ylabel(r'$x(t)$')
    if xlim:
        ax.set_xlim(xlim)
    if ylim:
        ax.set_ylim(ylim)
    if legend:
        ax.legend()
    if show:
        plt.show()
    return ax


def lin(start, stop, step):
    if start + step < start < stop or stop < start < start + step:
        raise ValueError()
    r = [start]
    while r[-1] + step < stop:
        r.append(r[-1] + step)
    return r
