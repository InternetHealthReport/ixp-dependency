import argparse
import logging
import os
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

sys.path.append('../')
from tools.shared_functions import (COLOR_FILL, COLORS, LARGE_IX_MARKER,
                                    MEDIUM_IX_MARKER, MEDIUM_IX_THRESHOLD,
                                    SMALL_IX_MARKER, SMALL_IX_THRESHOLD,
                                    annotate, sanitize_dir)

INPUT_FILE_SUFFIX = '.ixp_regionality.csv'
OUTPUT_FILE_SUFFIX = '.dependency_regionality_scatter.pdf'
DATA_DELIMITER = ','

mpl.rcParams['legend.markerscale'] = 1.25
mpl.rcParams['legend.handletextpad'] = 0
mpl.rcParams['axes.spines.right'] = True


def load_values(input_file: str) -> np.ndarray:
    return np.loadtxt(input_file,
                      delimiter=DATA_DELIMITER,
                      skiprows=1,
                      usecols=(0, 1, 2))


def plot_scatter(values: np.ndarray, ax: plt.Axes) -> None:
    small = values[values[:, 1] <= SMALL_IX_THRESHOLD]
    medium = values[(values[:, 1] > SMALL_IX_THRESHOLD) &
                    (values[:, 1] <= MEDIUM_IX_THRESHOLD)]
    large = values[values[:, 1] > MEDIUM_IX_THRESHOLD]
    large_ix_ids = list(large[:, 0])
    large_deps = large[:, 1]
    large_regionality = large[:, 2]

    ax.set_yscale('log')
    ax.set_ylabel('#Dependents')
    xmin = -0.05
    xmax = 1.05
    ymin = 8e-1
    ymax = 3e3
    fill_alpha = 0.4
    ax.fill_between((xmin, xmax),
                    0, SMALL_IX_THRESHOLD,
                    color=COLOR_FILL['small'],
                    alpha=fill_alpha)
    ax.fill_between((xmin, xmax),
                    SMALL_IX_THRESHOLD, MEDIUM_IX_THRESHOLD,
                    color=COLOR_FILL['medium'],
                    alpha=fill_alpha)
    ax.fill_between((xmin, xmax),
                    MEDIUM_IX_THRESHOLD, ymax,
                    color=COLOR_FILL['large'],
                    alpha=fill_alpha)

    ax2 = ax.twinx()
    ax2.hist(values[:, 2],
             bins=21,
             range=(-0.025, 1.025),
             align='mid',
             alpha=0.4,
             color='#31a354')
    ax2.grid(False)
    ax2.set_ylabel('#IXPs')

    ax.plot(small[:, 2], small[:, 1],
            linestyle='',
            marker=SMALL_IX_MARKER,
            color=COLORS['small'],
            label='Low')
    ax.plot(medium[:, 2], medium[:, 1],
            linestyle='',
            marker=MEDIUM_IX_MARKER,
            color=COLORS['medium'],
            label='Medium')
    ax.plot(large[:, 2], large[:, 1],
            linestyle='',
            marker=LARGE_IX_MARKER,
            color=COLORS['large'],
            label='High')

    annotate(31, 'DE-CIX Fr.', (15, -3), large_ix_ids,
             large_regionality, large_deps, ax, 0.005, 0)
    annotate(26, 'AMS-IX', (15, -3), large_ix_ids,
             large_regionality, large_deps, ax)
    annotate(18, 'LINX L1', (20, -10), large_ix_ids,
             large_regionality, large_deps, ax, 0.005, 0)
    annotate(171, 'IX.br SP', (-45, 15), large_ix_ids,
             large_regionality, large_deps, ax, -0.005, 0)

    ax.set_ylim(ymin, ymax)
    ax.set_ylabel('#Dependent ASes')
    ax.set_yscale('log')
    ax.grid(False, 'minor', 'y')

    ax.set_xlim(xmin, xmax)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(0.2))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.1))
    ax.set_xlabel('Regionality')

    ax.legend(ncol=3, loc='lower center', bbox_to_anchor=(0.5, 1))


def plot_histogram(values: np.ndarray, ax: plt.Axes) -> None:
    ax.hist(values[:, 2], 10, (0, 1))

    ax.set_xlim(-0.05, 1.05)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(0.1))
    ax.set_xlabel('Regionality')

    ax.yaxis.set_major_locator(ticker.MaxNLocator(5))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file')
    parser.add_argument('output_dir')
    args = parser.parse_args()

    FORMAT = '%(asctime)s %(levelname)s %(message)s'
    logging.basicConfig(
        format=FORMAT,
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    input_file = args.input_file
    output_dir = sanitize_dir(args.output_dir)
    output_file = f'{output_dir}' \
                  f'{os.path.basename(input_file)[:-len(INPUT_FILE_SUFFIX)]}' \
                  f'{OUTPUT_FILE_SUFFIX}'

    logging.info(f'Input file: {input_file}')
    logging.info(f'Output file: {output_file}')

    values = load_values(input_file)
    logging.info(f'Read {len(values)} IXPs')
    if len(values) == 0:
        sys.exit(0)

    # mpl.rcParams['figure.figsize'] = (6.4, 7)
    # fig = plt.figure()
    # gs = fig.add_gridspec(2, 1, height_ratios=(7, 3))
    # scatter_ax = fig.add_subplot(gs[0, 0])
    # hist_ax = fig.add_subplot(gs[1, 0], sharex=scatter_ax)
    fig, ax = plt.subplots()
    plot_scatter(values, ax)
    # plot_histogram(values, hist_ax)

    plt.savefig(output_file, bbox_inches='tight')


if __name__ == '__main__':
    main()
    sys.exit(0)
