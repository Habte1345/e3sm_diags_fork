from __future__ import print_function

import os

import matplotlib
import numpy as np
from cartopy.mpl.ticker import LatitudeFormatter

from e3sm_diags.driver.utils.general import get_output_dir
from e3sm_diags.logger import custom_logger
from e3sm_diags.plot import get_colormap

matplotlib.use("Agg")
import matplotlib.colors as colors  # isort:skip  # noqa: E402
import matplotlib.pyplot as plt  # isort:skip  # noqa: E402

logger = custom_logger(__name__)

plotTitle = {"fontsize": 11.5}
plotSideTitle = {"fontsize": 9.5}

# Position and sizes of subplot axes in page coordinates (0 to 1)
panel = [
    (0.1691, 0.6810, 0.6465, 0.2258),
    (0.1691, 0.3961, 0.6465, 0.2258),
    (0.1691, 0.1112, 0.6465, 0.2258),
]

# Border padding relative to subplot axes for saving individual panels
# (left, bottom, right, top) in page coordinates
border = (-0.06, -0.03, 0.13, 0.03)


def get_ax_size(fig, ax):
    bbox = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
    width, height = bbox.width, bbox.height
    width *= fig.dpi
    height *= fig.dpi
    return width, height


def plot_panel(n, fig, var, clevels, cmap, title, parameters, stats=None):

    mon = var.getTime()
    lat = var.getLatitude()
    var = np.transpose(var)

    # Contour levels
    levels = None
    norm = None
    if len(clevels) > 0:
        levels = [-1.0e8] + clevels + [1.0e8]
        norm = colors.BoundaryNorm(boundaries=levels, ncolors=256)

    # Contour plot
    ax = fig.add_axes(panel[n])
    cmap = get_colormap(cmap, parameters)
    # p1 = ax.contourf(
    p1 = ax.pcolor(
        mon,
        lat,
        var,
        norm=norm,
        cmap=cmap,
        edgecolors="face",
        shading="auto",
    )

    if title[0] is not None:
        ax.set_title(title[0], loc="left", fontdict=plotSideTitle)
    if title[1] is not None:
        ax.set_title(title[1], fontdict=plotTitle)
    if title[2] is not None:
        ax.set_title(title[2], loc="right", fontdict=plotSideTitle)

    mon_xticks = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]
    plt.xticks(mon, mon_xticks)
    lat_formatter = LatitudeFormatter()
    ax.yaxis.set_major_formatter(lat_formatter)
    ax.tick_params(labelsize=8.0, direction="out", width=1)
    ax.xaxis.set_ticks_position("bottom")
    ax.yaxis.set_ticks_position("left")

    # Color bar
    cbax = fig.add_axes((panel[n][0] + 0.6635, panel[n][1] + 0.0215, 0.0326, 0.1792))
    cbar = fig.colorbar(p1, cax=cbax, extend="both")
    w, h = get_ax_size(fig, cbax)

    if levels is None:
        cbar.ax.tick_params(labelsize=9.0, length=0)

    else:
        maxval = np.amax(np.absolute(levels[1:-1]))
        if maxval < 10.0:
            fmt = "%5.2f"
            pad = 25
        elif maxval < 100.0:
            fmt = "%5.1f"
            pad = 25
        else:
            fmt = "%6.1f"
            pad = 30
        cbar.set_ticks(levels[1:-1])
        labels = [fmt % level for level in levels[1:-1]]
        if all(x[-2:] == ".0" for x in labels):
            labels = [x[:-2] for x in labels]
            pad = pad - 5
        cbar.ax.set_yticklabels(labels, ha="right")
        cbar.ax.tick_params(labelsize=9.0, pad=pad, length=0)


def plot(reference, test, diff, metrics_dict, parameter):
    fig = plt.figure(figsize=parameter.figsize, dpi=parameter.dpi)

    plot_panel(
        0,
        fig,
        test,
        parameter.contour_levels,
        parameter.test_colormap,
        (parameter.test_name_yrs, parameter.test_title, test.units),
        parameter,
    )

    plot_panel(
        1,
        fig,
        reference,
        parameter.contour_levels,
        parameter.reference_colormap,
        (parameter.ref_name_yrs, parameter.reference_title, reference.units),
        parameter,
    )

    plot_panel(
        2,
        fig,
        diff,
        parameter.diff_levels,
        parameter.diff_colormap,
        (None, parameter.diff_title, None),
        parameter,
    )

    fig.suptitle(parameter.main_title, x=0.5, y=0.96, fontsize=18)

    # Save figure
    for f in parameter.output_format:
        f = f.lower().split(".")[-1]
        fnm = os.path.join(
            get_output_dir(parameter.current_set, parameter),
            parameter.output_file + "." + f,
        )
        plt.savefig(fnm)
        # Get the filename that the user has passed in and display that.
        fnm = os.path.join(
            get_output_dir(parameter.current_set, parameter),
            parameter.output_file + "." + f,
        )
        logger.info(f"Plot saved in: {fnm}")

    # Save individual subplots
    for f in parameter.output_format_subplot:
        fnm = os.path.join(
            get_output_dir(parameter.current_set, parameter),
            parameter.output_file,
        )
        page = fig.get_size_inches()
        i = 0
        for p in panel:
            # Extent of subplot
            subpage = np.array(p).reshape(2, 2)
            subpage[1, :] = subpage[0, :] + subpage[1, :]
            subpage = subpage + np.array(border).reshape(2, 2)
            subpage = list(((subpage) * page).flatten())
            extent = matplotlib.transforms.Bbox.from_extents(*subpage)
            # Save subplot
            fname = fnm + ".%i." % (i) + f
            plt.savefig(fname, bbox_inches=extent)

            orig_fnm = os.path.join(
                get_output_dir(parameter.current_set, parameter),
                parameter.output_file,
            )
            fname = orig_fnm + ".%i." % (i) + f
            logger.info(f"Sub-plot saved in: {fname}")

            i += 1

    plt.close()
