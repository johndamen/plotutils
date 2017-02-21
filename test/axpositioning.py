import unittest
from matplotlib import axes, figure
import plotutils


class TestPositioningAxes(unittest.TestCase):

    def test_create_from_axes(self):
        fig = figure.Figure(figsize=(6, 6))
        ax = axes.Axes(fig, [.1, .1, .8, .8])
        p = plotutils.PositioningAxes.from_axes(fig, ax, anchor='c')

        self.assertIsInstance(p, axes.Axes)
        self.assertEqual(p.bounds, (.1, .1, .8, .8))

        self.assertEqual(p.x, .5)
        self.assertEqual(p.y, .5)
        self.assertEqual(p.w, .8)
        self.assertEqual(p.h, .8)

    def test_create_from_axes2(self):
        fig = figure.Figure(figsize=(6, 6))
        ax = axes.Axes(fig, [.1, .1, .8, .8])
        p = plotutils.PositioningAxes.from_axes(fig, ax, anchor='ll')

        self.assertIsInstance(p, axes.Axes)
        self.assertEqual(p.bounds, (.1, .1, .8, .8))

        self.assertEqual(p.x, .1)
        self.assertEqual(p.y, .1)
        self.assertEqual(p.w, .8)
        self.assertEqual(p.h, .8)

    def test_create_new(self):
        fig = figure.Figure(figsize=(6, 6))
        bounds = (.1, .1, .8, .8)
        p = plotutils.PositioningAxes(fig, bounds, anchor='ll')
        self.assertEqual(p.bounds, bounds)
        self.assertEqual((p.x, p.y, p.w, p.h), bounds)

    def test_anchor(self):
        fig = figure.Figure(figsize=(6, 6))
        bounds = (.1, .1, .8, .8)
        p = plotutils.PositioningAxes(fig, bounds, anchor='ll')
        self.assertEqual(p.bounds, bounds)
        self.assertEqual((p.x, p.y, p.w, p.h), bounds)

        p.set_anchor_point('c')
        self.assertEqual((p.x, p.y, p.w, p.h), (.5, .5, .8, .8))

        p.set_anchor_point('ur')
        self.assertEqual((p.x, p.y, p.w, p.h), (.9, .9, .8, .8))

        p.set_anchor_point('ul')
        self.assertEqual((p.x, p.y, p.w, p.h), (.1, .9, .8, .8))

        p.set_anchor_point('lr')
        self.assertEqual((p.x, p.y, p.w, p.h), (.9, .1, .8, .8))
