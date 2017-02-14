from __future__ import print_function, division
from PyQt5 import QtGui, QtCore, QtWidgets
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from collections import OrderedDict
from functools import partial
import math
import multiprocessing as mp
import subprocess as sp
import os
import pickle
import sys


class PositioningAxes(Axes):

    _anchor_point = (0, 0)

    @classmethod
    def from_axes(cls, fig, a, **kwargs):
        return cls(fig, a.get_position().bounds, **kwargs)

    def __init__(self, fig, bounds, lock_aspect=False, anchor='ll', **kwargs):
        self._locked_aspect = lock_aspect
        self.set_anchor_point(anchor)
        super(PositioningAxes, self).__init__(fig, bounds, **kwargs)

    def set_anchor_point(self, pos=(0, 0)):
        """
        set reference point for x and y
        this can be entered as a tuple of axes coordinates
        ll: lower left  (0.0, 0.0)
        ul: upper left  (0.0, 1.0)
        ur: upper right (1.0, 1.0)
        lr: lower right (1.0, 0.0)
        c:  center      (0.5, 0.5)
        """
        posdict = dict(ll=(0, 0), ul=(0, 1), ur=(1, 1), lr=(1, 0), c=(.5, .5))
        if isinstance(pos, str):
            try:
                pos = posdict[pos]
            except KeyError:
                raise KeyError('invalid position name')
        if not isinstance(pos, tuple):
            raise TypeError('invalid position type')
        self._anchor_point = pos

    @property
    def bounds(self):
        """returns (xll, yll, w, h)"""
        return self._position.bounds
    @bounds.setter
    def bounds(self, v):
        """set new bounds"""
        self.set_position(v)

    def x2xll(self, x):
        """convert x position to xll based on anchor"""
        return x - self.w * self._anchor_point[0]

    def xll2x(self, xll):
        """convert xll to x position based on anchor"""
        return xll + self.w * self._anchor_point[0]

    def y2yll(self, y):
        """convert y position to yll based on anchor"""
        return y - self.h * self._anchor_point[1]

    def yll2y(self, yll):
        """convert yll to y position based on anchor"""
        return yll + self.h * self._anchor_point[1]

    @property
    def x(self):
        """x position as xll corrected for the anchor"""
        return self.xll2x(self.bounds[0])
    @x.setter
    def x(self, x):
        """reset the bounds with a new x value"""
        _, yll, w, h = self.bounds
        xll = self.x2xll(x)
        self.bounds = xll, yll, w, h

    @property
    def y(self):
        return self.yll2y(self.bounds[1])
    @y.setter
    def y(self, y):
        """reset the bounds with a new y value"""
        xll, _, w, h = self.bounds
        yll = self.y2yll(y)
        self.bounds = xll, yll, w, h

    @property
    def w(self):
        """width of the axes"""
        return self.bounds[2]
    @w.setter
    def w(self, w):
        """
        reset the bounds with a new width value
        the xll is corrected based on the anchor
        if the aspect ratio is locked, the height and yll are also adjusted
        """
        xll, yll, w0, h = self.bounds

        # adjust horizontal position based on anchor
        xll += self._anchor_point[0] * (w0 - w)

        # adjust height if aspect is locked
        if self._locked_aspect:
            h0, h = h, w / self.axaspect
            # adjust vertical position based on anchor
            yll += self._anchor_point[1] * (h0 - h)
        self.bounds = xll, yll, w, h

    @property
    def h(self):
        """height of the axes"""
        return self.bounds[3]
    @h.setter
    def h(self, h):
        """
        reset the bounds with a new height value
        the yll is corrected based on the anchor
        if the aspect ratio is locked, the width and xll are also adjusted
        """
        xll, yll, w, h0 = self.bounds

        # adjust vertical position based on anchor
        yll += self._anchor_point[1] * (h0 - h)

        # adjust width if aspect is locked
        if self._locked_aspect:
            w0, w = w, h * self.axaspect
            # adjust horizontal position based on anchor
            xll += self._anchor_point[0] * (w0 - w)
        self.bounds = xll, yll, w, h

    @property
    def figaspect(self):
        """aspect ratio of the figure"""
        fw, fh = self.figure.get_size_inches()
        return fw/fh

    @property
    def axaspect(self):
        """aspect ratio of the axes"""
        return self.figaspect / self.aspect

    @property
    def aspect(self):
        """real aspect ratio of figure and axes together"""
        _, _, aw, ah = self.bounds
        return self.figaspect * (aw/ah)

    def lock_aspect(self, b):
        """keep the aspect fixed"""
        self._locked_aspect = b

    def set_aspect_ratio(self, A, fix_height=False):
        """set the aspect ratio by adjusting width or height"""
        axaspect = A / self.figaspect

        if fix_height:
            self.w = self.h * axaspect
        else:
            self.h = self.w / axaspect

    def format_placeholder(self, label=''):
        """
        format the axes with no ticks and a simple label in the center
        the anchor point is shown as a blue circle
        """
        self.set_xticks([])
        self.set_yticks([])
        self.set_xlim(-1, 1)
        self.set_ylim(-1, 1)
        self.text(.5, .5, label, ha='center', va='center', transform=self.transAxes, zorder=2)

        ax, ay = self._anchor_point
        self.scatter([ax], [ay], marker='o', transform=self.transAxes, color=(.5, .5, .9), s=200, clip_on=False, zorder=1)


class AxPositioningEditor(QtWidgets.QMainWindow):

    position_dict = OrderedDict([
        ('ll', 'lower left'),
        ('ul', 'upper left'),
        ('ur', 'upper right'),
        ('lr', 'lower right'),
        ('c', 'center')])

    @classmethod
    def from_figaspect(cls, aspect, bounds=()):
        fig = Figure(figsize=(6, 6/aspect))
        return cls(fig, bounds=bounds)

    @classmethod
    def create_shape(cls, m, n, fig=None, figsize=None, figaspect=None):
        if fig is None:
            fig = Figure(figsize=figsize or (6, 6/(figaspect or 1)))

        bounds = []
        margin = .05
        boxmargin = .05
        bw = (1 - 2 * margin) / n
        bh = (1 - 2 * margin) / m
        for i in range(m): # rows
            for j in range(n): # cols
                bounds.append((margin + j * bw + boxmargin,
                               margin + i * bh + boxmargin,
                               bw - 2 * boxmargin,
                               bh - 2 * boxmargin))
        return cls(fig, bounds=bounds)


    def __init__(self, fig, bounds=()):
        super().__init__()
        self.anchor = 'c'
        w, h = fig.get_size_inches()
        self.figure = fig
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setFixedSize(400, 400 / (w / h))

        self.canvas.mpl_connect('button_release_event', self.draw_axes)
        self.pointing_axes = False

        self.create_axes(bounds)
        self.build()

    def get_bounds(self):
        bounds = []
        for n, a in self.axes.items():
            bounds.append(a.bounds)
        return bounds

    def pycode_bounds(self):
        boundstr = ''
        for n, a in self.axes.items():
            kwargs = dict(zip(['xll', 'yll', 'w', 'h'], a.bounds), name=n)
            boundstr += '    ({xll:.3f}, {yll:.3f}, {w:.3f}, {h:.3f})  # {name}\n'.format(**kwargs)
        return 'bounds = [\n'+boundstr+']'

    def draw_axes(self, event):
        if self.pointing_axes:
            x, y = self.figure.transFigure.inverted().transform((event.x, event.y))
            self.add_axes(x, y)
            self.pointing_axes = False

    def build(self):
        w = QtWidgets.QWidget()
        self.setCentralWidget(w)
        self.layout = QtWidgets.QHBoxLayout(w)
        self.layout.setSpacing(5)

        canvas_layout = QtWidgets.QVBoxLayout()
        self.layout.addLayout(canvas_layout)
        canvas_layout.addWidget(self.canvas)
        canvas_layout.addItem(QtWidgets.QSpacerItem(
            0, 0, QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Expanding))

        self.edit_axes_layout = QtWidgets.QVBoxLayout()
        self.layout.addLayout(self.edit_axes_layout)

        self.layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum))

        self.position_group = QtWidgets.QGroupBox()
        self.edit_axes_layout.addWidget(self.position_group)
        group_layout = QtWidgets.QVBoxLayout(self.position_group)
        radio_buttons = dict()
        for pos, name in self.position_dict.items():
            radio_buttons[pos] = rw = QtWidgets.QRadioButton(name)
            rw.clicked.connect(partial(self.update_anchor, pos))
            group_layout.addWidget(rw)

        self.axfields = AxPositionFieldBox(self.axes)
        self.axfields.changed.connect(self.draw)
        self.axfields.deleted.connect(self.delete_axes)
        self.edit_axes_layout.addWidget(self.axfields)
        # self.axfields = dict()
        # for name, a in self.axes.items():
        #     self.axfields[name] = w = AxPositionEditor(name, a)
        #     w.changed.connect(self.draw)
        #     w.deleted.connect(self.delete_axes)
        #     self.edit_axes_layout.addWidget(w)

        self.add_axes_button = AddAxesButton()
        self.add_axes_button.setFlat(True)
        self.add_axes_button.clicked.connect(self.add_axes_clicked)
        self.edit_axes_layout.addWidget(self.add_axes_button)

        self.edit_axes_layout.addItem(QtWidgets.QSpacerItem(
            0, 0, QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Expanding))

        radio_buttons[self.anchor].click()

    def add_axes_clicked(self):
        QtWidgets.QMessageBox.information(self, 'New axes',
                                      'Click on the canvas to position a new axes')
        self.pointing_axes = True

    def add_axes(self, x, y):
        axnames = list(self.axes.keys())
        for i in range(50):
            n = chr(65 + i)
            if n not in axnames:
                self.axes[n] = PositioningAxes(self.figure, [x - .3, y - .3, .4, .4], anchor=self.anchor)
                self.draw(posfields=True)
                return

    def update_anchor(self, pos, clicked):
        if clicked:
            for name, a in self.axes.items():
                a.set_anchor_point(pos)
                self.anchor = pos
        self.draw()
        self.axfields.update_fields()

    def create_axes(self, bounds):
        self.axes = OrderedDict()
        for i, bnd in enumerate(bounds):
            a = PositioningAxes(self.figure, bnd, anchor=self.anchor)
            self.axes[chr(65 + i)] = a

        self.draw()

    def draw(self, posfields=False):
        self.figure.clear()
        for name, a in self.axes.items():
            a.format_placeholder(name)
            self.figure.add_axes(a)
        self.canvas.draw_idle()

        if posfields:
            self.axfields.clear()
            self.axfields.fill()

    def delete_axes(self, axeditor):
        axeditor.deleteLater()
        self.axes.pop(axeditor.name)
        self.draw()


class AxPositionFieldBox(QtWidgets.QGroupBox):

    changed = QtCore.pyqtSignal()
    deleted = QtCore.pyqtSignal(object)

    def __init__(self, axes):
        super().__init__()
        if not isinstance(axes, dict):
            raise TypeError('axes not a dict instance')
        self.axes = axes
        self.axfields = dict()

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setSpacing(5)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.fill()

    def clear(self):
        for i in reversed(range(self.layout.count())):
            w = self.layout.itemAt(i).widget()
            w.setParent(None)
            w.deleteLater()

    def fill(self, axes=None):
        if axes is not None:
            self.axes = axes

        for n in sorted(self.axes.keys()):
            a = self.axes[n]
            self.axfields[n] = w = AxPositionField(n, a)
            w.changed.connect(self.changed.emit)
            w.deleted.connect(self.deleted.emit)
            self.layout.addWidget(w)

    def update_fields(self):
        for name, f in self.axfields.items():
            f.update_fields()


class AddAxesButton(QtWidgets.QPushButton):

    def __init__(self):
        super().__init__('Add new axes')
        self.setFlat(True)


class AxPositionField(QtWidgets.QWidget):

    changed = QtCore.pyqtSignal()
    deleted = QtCore.pyqtSignal(object)

    def __init__(self, name, a):
        if not isinstance(a, PositioningAxes):
            raise TypeError('invalid axes type; not an instance of AxesPositioner')
        self.name = name
        self.ax = a
        super().__init__()
        self.build()

    def build(self):
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setSpacing(5)
        self.layout.setContentsMargins(0, 0, 0, 0)
        label = QtWidgets.QLabel(self.name+': ')
        self.layout.addWidget(label)

        self.fields = dict()
        for n in 'xywh':
            self.fields[n] = f = LabeledFloatField(n, getattr(self.ax, n))
            f.changed.connect(partial(self.update_axes_pos, n))
            self.layout.addWidget(f)

        self.fields['aspect'] = f = LabeledFloatField('A', self.ax.aspect)
        f.changed.connect(partial(self.update_axes_aspect, 'aspect'))
        self.layout.addWidget(f)

        self.delete_button = QtWidgets.QPushButton('x')
        self.delete_button.setFlat(True)
        self.delete_button.clicked.connect(self.delete_axes)
        self.layout.addWidget(self.delete_button)

    def delete_axes(self):
        self.deleted.emit(self)

    def update_axes_aspect(self, n, v):
        self.ax.set_aspect_ratio(v)
        self.update_fields()
        self.changed.emit()

    def update_axes_pos(self, n, v):
        setattr(self.ax, n, v)
        self.update_fields()
        self.changed.emit()

    def update_fields(self):
        for n, f in self.fields.items():
            f.set_value(getattr(self.ax, n))

    def deleteLater(self):
        for i in reversed(range(self.layout.count())):
            w = self.layout.itemAt(i).widget()
            w.setParent(None)
            w.deleteLater()


class FloatField(QtWidgets.QLineEdit):

    changed = QtCore.pyqtSignal(float)

    def __init__(self, v, fmt='{:.3f}', width=45):
        super().__init__()
        self.fmt = fmt
        self.val = float(v)
        self.set_value(v)
        self.setFixedWidth(width)
        self.editingFinished.connect(self.check_change)

    def check_change(self):
        """
        check if value is changed
        update value and emit changed signal if field text is different from
        the formatted value
        """

        # compare content to value
        if self.text() == self.fmt.format(self.val):
            return
        else:
            # update value
            self.val = float(self.text())

            # emit signal
            self.changed.emit(self.val)

    def value(self):
        """return the value after checking for change"""
        self.check_change()
        return self.val

    def set_value(self, v):
        """set a value as a float and update field"""
        self.val = float(v)
        self.setText(self.fmt.format(self.val))


class LabeledFloatField(QtWidgets.QWidget):

    changed = QtCore.pyqtSignal(float)

    def __init__(self, name, v, **kwargs):
        super().__init__()
        l = QtWidgets.QHBoxLayout(self)
        l.setSpacing(3)
        l.setContentsMargins(0, 0, 0, 0)
        self.label = QtWidgets.QLabel(name)
        l.addWidget(self.label)
        self.value_field = FloatField(v, **kwargs)
        l.addWidget(self.value_field)
        self.value_field.changed.connect(self.changed.emit)

    def value(self):
        return self.value_field.value()

    def set_value(self, v):
        return self.value_field.set_value(v)

    def deleteLater(self):
        self.value_field.deleteLater()
        self.label.deleteLater()
        super().deleteLater()



# def _position_axes_window(figsize, bounds, **kwargs):
    # app = QtGui.QApplication([])
    # w = AxPositioningEditor(Figure(figsize=fig.get_size_inches()), bounds, **kwargs)
    # w.show()

    # try:
    #     app.exec()
    #     print(w.pycode_bounds())
    #     pipe.send(w.get_bounds())
    # finally:
    # w.deleteLater()


def _subprocess_open_window(*args, **kwargs):
    loc, name = os.path.split(__file__)
    p = sp.Popen(['python', '-m', name, 'window'], cwd=loc)
    p.communicate(pickle.dump((args, kwargs)))
    p.wait()


def open_window(figsize, bounds, **kwargs):
    if isinstance(figsize, Figure):
        figsize = figsize.get_size_inches()
    app = QtWidgets.QApplication([])
    w = AxPositioningEditor(Figure(figsize=figsize), bounds, **kwargs)
    w.show()

    try:
        app.exec()
        print(w.pycode_bounds())
        # sys.stdout.write(pickle.dump(w.get_bounds())+'\n')
    finally:
        w.deleteLater()


def adjust_axes(fig, **kwargs):
    axes = fig.get_axes()
    bounds = [a.get_position().bounds for a in axes]

    _subprocess_open_window(fig.get_size_inches(), bounds, **kwargs)

    newbounds = bounds

    for a in axes[len(newbounds):]:
        fig.delaxes(a)

    for i, bnd in enumerate(newbounds):
        try:
            axes[i].set_position(bnd)
        except IndexError:
            fig.add_axes(bnd)



if __name__ == '__main__':

    w, h = .26, .8
    bounds = [
        (.08, .10, w, h),
        (.36, .10, w, h),
        (.64, .10, w, h),
        (.92, .10, .02, h)
    ]
    open_window((12, 4), bounds)


    # import sys
    # import pickle
    # argv = sys.argv[1:]
    # if argv and argv[0] == 'window':
    #     figsize, bounds, kwargs = pickle.load(sys.stdin)
    #     print(figsize, bounds, kwargs)
    #     # app = QtGui.QApplication([])
    #     # w = AxPositioningEditor(Figure(figsize=figsize), bounds, **kwargs)
    #     # w.show()
    #     #
    #     # try:
    #     #     app.exec()
    #     #     for bnd in w.get_bounds():
    #     #         s = '({:.3f}, {:.3f}, {:.3f}, {:.3f})\n'.format(*bnd)
    #     #         sys.stdout.write(s)
    #     # finally:
    #     #     w.deleteLater()
    # else:
    #     # from matplotlib import pyplot as plt
    #     # fig = plt.figure()
    #     # ax = plt.subplot(1, 2, 1)
    #     # ax = plt.subplot(2, 2, 2)
    #     # ax = plt.subplot(2, 2, 4)
    #     #
    #     # adjust_axes(fig)
    #
    #
    #     # plt.show()