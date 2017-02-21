from matplotlib import pyplot as plt
import plotutils

fig = plt.figure()
ax = fig.add_axes([.1, .1, .8, .8])
p = plotutils.PositioningAxes.from_axes(fig, ax, anchor='c')

p.set_anchor_point('c')
print(p.x, p.y)

p.set_anchor_point('ll')
print(p.x, p.y)

p.set_anchor_point('ur')
print(p.x, p.y)