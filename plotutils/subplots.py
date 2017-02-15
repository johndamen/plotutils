import numpy as np
from matplotlib import pyplot as plt


def hsubplots(figwidth, shape, hpad=0, vpad=0, box=(0, 0, 1, 1), ax_aspect=1):
    """
    calculate axes positions for a fixed width
    figure height is dependent on the subplot axes and spacings

    :param figwidth: width in inches of figure to build
    :param shape: (rows, cols)
    :param hpad: horizontal padding
    :param vpad: vertical padding
    :param box: (xll, yll, xur, yur)
    :param ax_aspect: aspect of individual axes
    :return: figsize (w, h), axpositions (3D array)
             positions are returned as a 3D array of row, col, subplot box

    >>>from matplotlib import pyplot as plt
    >>>figsize, positions = hsubplots(10, (2, 3), box=(.05, .05, .95, .95))
    >>>fig = plt.figure(figsize=figsize)
    >>>for i, rowpos in enumerate(positions):
    >>>    for j, pos in enumerate(rowpos):
    >>>        fig.add_axes(pos)
    >>>plt.show()
    """
    m, n = shape

    box = np.array(box)

    axwidth = (box[2] - box[0] - hpad * (n - 1)) / n
    axheight = (box[3] - box[1] - vpad * (m - 1)) / m
    figheight = figwidth * (axwidth / axheight) * ax_aspect

    axpos = []
    for i in range(m):  # rows
        axpos.append([])
        for j in range(n):  # cols
            x = box[0] + j * axwidth + j * hpad
            y = box[1] + i * axheight + i * vpad
            axpos[-1].append([x, y, axwidth, axheight])

    return (figwidth, figheight), np.array(axpos[::-1])


def xyshared_plots(shape, axes, datasets, plotfn, xlabel, ylabel, labels=False, labeldict=None):
    m, n = shape

    if labels == '1A':
        labels = [str(i + 1) + chr(65 + j) for i in range(m) for j in range(n)]
    elif labels == 'A1':
        labels = [chr(65 + i) + str(j + 1) for i in range(m) for j in range(n)]
    elif labels == 'A':
        labels = [chr(65 + i * n + j) for i in range(m) for j in range(n)]

    for mi in range(m):
        for ni in range(n):
            # calculate flat index
            i = mi * n + ni

            # get axes and dataset for this index
            ax = axes[i]
            d = datasets[i]

            # plot dataset on axes
            r = plotfn(ax, d)

            # apply label annotation
            if isinstance(labels, list):
                annotate(ax, labels[i], **(labeldict or {}))

            # apply ticks and axlabels
            if mi == (m - 1):
                ax.set_xlabel(xlabel)
            else:
                ax.set_xticklabels([])

            if ni == 0:
                ax.set_ylabel(ylabel)
            else:
                ax.set_yticklabels([])
    return r


def annotate(ax, label, offset=.065, dx=0, dy=0, boxwidth=.1, shape='none', case='upper', **kwargs):
    """
    annotate an axes in the upper left corner with the specified label
    :param ax: axes to apply label to
    :param label: the label to apply (is converted to a string)
    :param offset: offset from the corner
    :param dx: hor offset of the text from the surrounding box
    :param dy: vert offset of the text from the surrounding box
    :param boxwidth: width of the surrounding box
    :param shape: shape of the surrounding box (cicle|square|none)
    :param kwargs: keyword arguments for text and patch
                   possible text arguments are fontsize, usetex, fontdict
                   other arguments are passed to the relevant patch
    """
    x, y = (0 + offset, 1 - offset)

    font_kwargs = {k: kwargs.pop(k) for k in kwargs.keys() if k in ('fontsize', 'usetex', 'fontdict')}
    label = str(label)
    if case == 'upper':
        label = label.upper()
    elif case == 'lower':
        label = label.lower()

    kwargs.setdefault('ec', 'none')
    kwargs.setdefault('fc', 'w')

    if shape == 'none':
        pass
    elif shape == 'circle':
        ax.add_patch(plt.Circle((x, y), radius=.5*boxwidth, transform=ax.transAxes, **kwargs))
    elif shape == 'square':
        ax.add_patch(plt.Rectangle((x-.5*boxwidth, y-.5*boxwidth), boxwidth, boxwidth, **kwargs))
    else:
        raise ValueError('invalid shape')

    ax.text(x + dx, y + dy, label,
            ha='center', va='center', zorder=3, transform=ax.transAxes, **font_kwargs)


if __name__ == '__main__':
    from matplotlib import pyplot as plt
    figsize, positions = hsubplots(10, (3, 3), hpad=.05, vpad=.05, box=(.08, .07, .9, .95))
    fig = plt.figure(figsize=figsize)
    for i, rowpos in enumerate(positions):
        for j, pos in enumerate(rowpos):
            ax = fig.add_axes(pos)
            annotate(ax, 'A', shape='circle', fc='r', fontsize=12)
    plt.show()


    def plotter(ax, dataset):
        r = ax.scatter(dataset['x'], dataset['y'], c=dataset['z'], cmap='inferno', lw=0)
        ax.set_xticks([0, .5, 1])
        ax.set_yticks([0, .5, 1])
        ax.set_xlim(-.1, 1.1)
        ax.set_ylim(-.1, 1.1)
        return r

    figsize, positions = hsubplots(10, (3, 3), hpad=.01, vpad=.01, box=(.08, .07, .9, .95))
    fig = plt.figure(figsize=figsize)
    cax = fig.add_axes([.91, .07, .02, .88])
    axes = []
    datasets = []
    labels = []

    m, n = positions.shape[:2]
    for i, rowpos in enumerate(positions):
        for j, pos in enumerate(rowpos):
            ax = fig.add_axes(pos)
            axes.append(ax)
            datasets.append(dict(x=np.random.rand(100), y=np.random.rand(100), z=np.random.rand(100)))
            labels.append(chr(65 + i * n + j))
    c = xyshared_plots((m, n), axes, datasets, plotter, 'xlabel', 'ylabel', labels='A1')
    plt.colorbar(c, cax=cax).set_label('z')
    plt.show()

