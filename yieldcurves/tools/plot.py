# -*- coding: utf-8 -*-

# yieldcurves
# -----------
# A Python library for financial yield curves.
#
# Author:   sonntagsgesicht
# Version:  0.2.2, copyright Thursday, 22 August 2024
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


def lin(start, stop=None, step=None, num=1_000):
    if isinstance(start, slice):
        start, stop, step = start.start, start.stop, start.step
    if stop is None:
        if start < 0:
            stop = 0
        else:
            start, stop = 0, start
    if step is None:
        step = (stop - start) / num
    if start + step < start < stop or stop < start < start + step:
        raise ValueError()
    r = [start]
    while r[-1] + step < stop:
        r.append(r[-1] + step)
    return r


def plot(x, *curve, legend=True, figsize=(10, 5), kind='plot', backend=None,
         params=None, show=True, xlim=(), ylim=(), **curves):
    if backend:
        use(backend)
    fig, ax = plt.subplots(figsize=figsize)
    plot = getattr(ax, kind)
    if isinstance(x, (int, float, slice)):
        x = lin(x)
    x = tuple(x)
    params = params or {}
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


class Plotter:

    def __init__(self, x, legend=True, figsize=(10, 5), kind='plot',
                 backend=None, params=None, show=True, xlim=(), ylim=()):
        self.x = lin(x) if isinstance(x, (int, float, slice)) else x
        self.legend = legend
        self.figsize = figsize
        self.kind = kind
        self.backend = backend
        self.params = params
        self.show = show
        self.xlim = xlim
        self.ylim = ylim

    def __call__(self, *curve, **curves):
        return plot(self.x, *curve, legend=self.legend, figsize=self.figsize,
                    kind=self.kind, backend=self.backend, params=self.params,
                    show=self.show, xlim=self.xlim, ylim=self.ylim, **curves)

    def __getitem__(self, item):
        return Plotter(item)


plotter = Plotter(25)
