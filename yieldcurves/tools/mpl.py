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


class Plotter:

    def __init__(self, x):
        self.x = x

    def __call__(self, *curve, legend=True, figsize=(10, 5), kind='plot',
                 backend=None, params=(), show=True, xlim=(), ylim=(),
                 **curves):
        return plot(self.x, *curve, legend=legend, figsize=figsize,
                    kind=kind, backend=backend, params=params, show=show,
                    xlim=xlim, ylim=ylim, **curves)

    def __getitem__(self, item):
        if not isinstance(item, slice):
            item = slice(item)
        start, stop, step = item.start, item.stop, item.step
        if start is None:
            start = 0.
        if stop is None:
            stop = 1.
        if step is None:
            step = (stop - start) / 100
        x = lin(start, stop, step)
        return Plotter(x)


plotter = Plotter(lin(0., 1., 0.01))
