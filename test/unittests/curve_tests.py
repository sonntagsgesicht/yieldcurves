# -*- coding: utf-8 -*-

# yieldcurves
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.4, copyright Saturday, 10 October 2020
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


from unittest import TestCase

from yieldcurves.interpolation import linear
from yieldcurves.curve import CurveAdapter, \
    CurveAlgebra, init_curve, call_wrapper_builder


def lin(start, stop, step):
    r = [start]
    while r[-1] + step < stop:
        r.append(r[-1] + step)
    return r


class AggregateDict(dict):

    func = sum

    def __call__(self, *_, **__):
        return self.__class__.func(self.values())


class CurveUnitTests(TestCase):
    def setUp(self):
        self.x_list = lin(0.01, 2.9, 0.2)
        self.y_list = [0.017, 0.016, 0.015, 0.0155, 0.0165] * len(self.x_list)
        self.y_list = self.y_list[:len(self.x_list)]
        self.grid = lin(0.01, 3.0, 0.1)
        self.places = 7

    def call_test(self, f, g, grid=None):
        if grid is None:
            grid = self.grid
        for x in grid:
            self.assertAlmostEqual(f(x), g(x), places=self.places)

    def transform_test(self, f, g, grid=None):
        # call and transform methods
        self.assertEqual(g(1), f(1))
        self.call_test(f, g)
        g = CurveAdapter(f, pre=lambda _: 2 * _)

        self.assertEqual(g(1), f(2))
        for x in f:
            self.assertEqual(g[x / 2], f[x])
            self.assertRaises(KeyError, g.__getitem__, x)

        g = CurveAdapter(f, pre=lambda _: float(_))
        for x in f:
            self.assertRaises(KeyError, f.__getitem__, str(x))
            self.assertEqual(g[str(x)], f[x])

        if grid is None:
            grid = self.grid
        for x in grid:
            self.assertAlmostEqual(f(x), g(str(x)), places=self.places)

    def call_dict_test(self, f, g):
        for x, y in zip(f, g):
            self.assertAlmostEqual(x, y)
            self.assertAlmostEqual(f[x], f(x))
            self.assertAlmostEqual(f[y], g(y))

        # __setitem__
        i = tuple(f)[int(len(f) / 2)]
        v = 99.99
        f[i] = v
        self.assertAlmostEqual(v, f(i))
        self.assertAlmostEqual(v, g(i))

    def dict_test(self, f, g):
        # __len__
        self.assertEqual(len(f), len(g))

        # __iter__
        # __getitem__
        for x, y in zip(f, g):
            self.assertAlmostEqual(x, y)
            self.assertAlmostEqual(f[x], g[y])

        if len(f):
            # __setitem__
            i = tuple(f)[int(len(f) / 2)]
            v = 99.99
            f[i] = v
            self.assertAlmostEqual(v, f[i])
            self.assertAlmostEqual(v, g[i])
            vv = g.pop(i)
            self.assertAlmostEqual(v, vv)
            self.assertFalse(i in g)
            f[i] = v

        # __contains__
        if len(f):
            self.assertTrue(i in f)
            self.assertTrue(i in g)

        # __delitem__
        if len(f):
            del f[i]
            self.assertFalse(i in f)
            self.assertFalse(i in g)
            v = 101.101
            g[i] = v
            self.assertTrue(i in f)
            self.assertTrue(i in g)
            del g[i]
            self.assertFalse(i in f)
            self.assertFalse(i in g)

        # dict methods
        for i in g.keys():
            self.assertTrue(i in f)
            self.assertTrue(i in g)

        for v in g.values():
            self.assertTrue(v in self.y_list)

        for k, v in g.items():
            self.assertTrue(k in f)
            self.assertTrue(k in g)
            self.assertEqual(v, g[k])
            self.assertTrue(k in self.x_list)
            self.assertTrue(v in self.y_list)

        g.update({100: 0.0})
        if len(g):
            self.assertEqual(0.0, g[100])

    def test_CurveAdapter(self):
        # init
        f = linear(self.x_list, self.y_list)
        g = CurveAdapter(f)

        self.assertEqual(g, init_curve(g))
        self.assertNotEqual(g, 0.0)

        self.assertTrue(g)
        self.assertFalse(init_curve(0.0))

        f = float(init_curve(0.0))
        self.assertEqual(0.0, f)

        f = linear(self.x_list, self.y_list)
        g = CurveAdapter(f)

        self.call_test(f, g)
        self.dict_test(f, g)
        self.call_dict_test(f, g)
        self.transform_test(f, g)

        g = CurveAdapter(linear([1.0, 1.1], [0.1, 0.2]))
        s = 'CurveAdapter(linear([1.0, 1.1], [0.1, 0.2]))'
        self.assertEqual(s, str(g))
        r = 'CurveAdapter(linear([1.0, 1.1], [0.1, 0.2]))'
        self.assertEqual(r, repr(g))

    def test_ConstantCurve(self):
        # init
        value = 0.02
        f = AggregateDict({None: value})
        g = CurveAdapter(f)
        self.call_test(f, g)
        self.dict_test(f, g)

        f = (lambda _: value)
        g = CurveAdapter(value)
        self.call_test(f, g)
        self.dict_test(dict(), g)

        g = CurveAdapter(value, call=lambda c, *_, **__: c * c)
        self.assertEqual(value * value , g())

        # str and repr methods
        self.assertEqual('0.02', str(g))
        self.assertEqual('0.02', repr(g))

    def test_AlgebraCurve(self):
        c = CurveAdapter(linear(self.x_list, self.y_list))
        a, s, m, d = 0.02, 0.001, 2, 4
        v = 2

        f = CurveAlgebra(CurveAdapter(v * m))
        g = CurveAlgebra(CurveAdapter(v), leverage=m)
        self.call_test(f, g)

        f = CurveAlgebra(CurveAdapter(v + a))
        g = CurveAlgebra(CurveAdapter(v), spread=a)
        self.call_test(f, g)

        f = CurveAlgebra(CurveAdapter(v * m + a))
        g = CurveAlgebra(CurveAdapter(v), spread=a, leverage=m)
        self.call_test(f, g)

        f = CurveAlgebra(CurveAdapter(v * m + a))
        g = CurveAlgebra(CurveAdapter(v), add=[a], mul=[m])
        self.call_test(f, g)

        f = CurveAlgebra(CurveAdapter(v * m * m + a + a))
        g = CurveAlgebra(CurveAdapter(v), add=[a, a], mul=[m, m])
        self.assertEqual(len(g.add), 2)
        self.call_test(f, g)

        f = CurveAlgebra(CurveAdapter(v * m / d + a - s))
        g = CurveAlgebra(CurveAdapter(v), add=[a, a], mul=[m, m])
        g = g / m
        g = g - a
        self.assertEqual(len(g.add), 1)
        self.assertEqual(len(g.sub), 0)
        self.assertEqual(len(g.mul), 1)
        self.assertEqual(len(g.div), 0)
        g = g - s
        g = g / d
        self.assertEqual(len(g.add), 1)
        self.assertEqual(len(g.sub), 1)
        self.assertEqual(len(g.mul), 1)
        self.assertEqual(len(g.div), 1)
        self.call_test(f, g)

        f = CurveAlgebra(c, add=[CurveAdapter(a)])
        g = CurveAlgebra(c, spread=a)
        self.call_test(f, g)

        f = CurveAlgebra(c, sub=[CurveAdapter(s)])
        g = CurveAlgebra(c, spread=-s)
        self.call_test(f, g)

        f = CurveAlgebra(c, mul=[CurveAdapter(m)])
        g = CurveAlgebra(c, leverage=m)
        self.call_test(f, g)

        f = CurveAlgebra(c, div=[CurveAdapter(d)])
        g = CurveAlgebra(c, leverage=1/d)
        self.call_test(f, g)

        g = CurveAlgebra(c, div=[CurveAdapter(d)], sub=[CurveAdapter(s)])
        g = g + CurveAdapter(s)
        g = g * CurveAdapter(d)
        self.call_test(c, g)

        # init
        g = init_curve(123.4)
        gg = CurveAlgebra(g, spread=1.0, leverage=1.1)
        ggg = CurveAlgebra(gg, spread=2.0)
        self.assertEqual(gg.curve, ggg.curve)
        self.assertEqual(gg.leverage, ggg.leverage)
        self.assertNotEqual(gg.spread, ggg.spread)

        # add sub mul div
        gg = CurveAlgebra(g) + init_curve(1.)
        self.assertEqual(g(0) + 1., gg(0))

        gg = CurveAlgebra(g) - init_curve(1.)
        self.assertEqual(g(0) - 1., gg(0))

        gg = CurveAlgebra(g) * init_curve(1.1)
        self.assertEqual(g(0) * 1.1, gg(0))

        gg = CurveAlgebra(g) / init_curve(1.1)
        self.assertEqual(g(0) / 1.1, gg(0))

        # spread leverage
        gg = CurveAlgebra(g, spread=1.1)
        self.assertEqual(g(0) + 1.1, gg(0))

        gg = CurveAlgebra(g, leverage=1.1)
        self.assertEqual(g(0) * 1.1, gg(0))

        # str and repr methods
        g = CurveAdapter(linear([1.0, 1.1], [0.1, 0.2]))
        g = CurveAlgebra(g) + CurveAdapter(linear([1.0], [0.01]))
        s = 'CurveAdapter(linear([1.0, 1.1], [0.1, 0.2])) ' \
            '+ CurveAdapter(linear([1.0], [0.01]))'
        self.assertEqual(s, str(g))
        r = 'CurveAdapter(linear([1.0, 1.1], [0.1, 0.2])) ' \
            '+ CurveAdapter(linear([1.0], [0.01]))'
        self.assertEqual(r, repr(g))

    def test_init_curve(self):
        v = 0.01
        c = init_curve(v)
        self.assertTrue(isinstance(c, CurveAdapter))
        self.assertNotEqual(type(c), type(v))
        self.assertEqual(c.curve, v)
        cc = init_curve(c)
        self.assertTrue(isinstance(c, CurveAdapter))
        self.assertEqual(type(c), type(cc))
        self.assertEqual(c, cc)

    def test_call_wrapper(self):
        c = CurveAdapter(linear([1, 2], [0.01, 0.02]))
        d = CurveAdapter(linear([1, 2, 3], [0.01, 0.02, 0.03]))
        self.assertEqual(None, c.get(0.03, None))
        self.assertEqual(0.03, d.get(3, None))

        get = CurveAdapter(c, call='get')
        self.assertEqual(None, get(0.03))

        getter = call_wrapper_builder('getter', 'get')
        self.assertEqual(None, getter(c)(0.03))

        getter = call_wrapper_builder('get')
        self.assertEqual(None, getter(c)(0.03))
        self.assertEqual(0.03, getter(d)(3))
