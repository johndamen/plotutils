from matplotlib import pyplot as plt
import plotutils

fig = plt.figure()
ax = fig.add_axes([.1, .1, .8, .8])
p = plotutils.PositioningAxes.from_axes(fig, ax, anchor='c')

p.set_anchor('C')
print(p.x, p.y)

p.set_anchor('SW')
print(p.x, p.y)

p.set_anchor('NE')
print(p.x, p.y)