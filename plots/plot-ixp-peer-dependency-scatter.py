import argparse
import logging
import os
import sys
from typing import Tuple

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

sys.path.append('../')
from tools.shared_functions import (COLOR_FILL, COLORS, LARGE_IX_MARKER,
                                    MEDIUM_IX_MARKER, MEDIUM_IX_THRESHOLD,
                                    SMALL_IX_MARKER, SMALL_IX_THRESHOLD,
                                    annotate, sanitize_dir)

INPUT_FILE_SUFFIX = '.ixp_table.csv'
OUTPUT_FILE_SUFFIX = '.ixp_peer_dependency_scatter'
PLOT_FILE_SUFFIX = '.pdf'
STAT_FILE_SUFFIX = '.csv'
DATA_DELIMITER = ','

mpl.rcParams['legend.markerscale'] = 1.25
mpl.rcParams['legend.handletextpad'] = 0
mpl.rcParams['legend.columnspacing'] = 1


def load_ixp_table(ixp_table_files) -> Tuple[list, list, list]:
    small = list()
    medium = list()
    large = list()
    with open(ixp_table_files, 'r') as f:
        f.readline()
        for line in f:
            line_split = line.strip().split(DATA_DELIMITER)
            peers = int(line_split[5])
            dependencies = int(line_split[12])
            peers_seen_r = float(line_split[20])
            if peers <= 1 or dependencies == 0 or peers_seen_r == 0:
                continue
            ix_id = line_split[0]
            value = (peers, peers_seen_r, dependencies, ix_id)
            if dependencies <= SMALL_IX_THRESHOLD:
                small.append(value)
            elif dependencies <= MEDIUM_IX_THRESHOLD:
                medium.append(value)
            else:
                large.append(value)
    return small, medium, large


def plot_scatter(ixp_values: Tuple[list, list, list],
                 output_dir: str,
                 output_file_prefix: str) -> None:

    if ixp_values[0]:
        small_peers, small_peers_seen_r, small_deps, small_ix_ids = zip(*ixp_values[0])
    else:
        small_peers = small_deps = tuple()
    if ixp_values[1]:
        medium_peers, medium_peers_seen_r, medium_deps, _ = zip(*ixp_values[1])
    else:
        medium_peers = medium_deps = tuple()
    if ixp_values[2]:
        large_peers, large_peers_seen_r, large_deps, large_ix_ids = zip(*ixp_values[2])
    else:
        large_peers = large_deps = large_ix_ids = tuple()

    fig, ax = plt.subplots()

    ax.plot(small_peers,
            small_deps,
            color=COLORS['small'],
            label=f'Low',
            linestyle='',
            marker=SMALL_IX_MARKER)
    ax.plot(medium_peers,
            medium_deps,
            color=COLORS['medium'],
            label=f'Medium',
            linestyle='',
            marker=MEDIUM_IX_MARKER)
    ax.plot(large_peers,
            large_deps,
            color=COLORS['large'],
            label=f'High',
            linestyle='',
            marker=LARGE_IX_MARKER)
    annotate('31', 'DE-CIX Fr.', (-90, -5), large_ix_ids,
             large_peers, large_deps, ax, -30, 0)
    annotate('26', 'AMS-IX', (-100, -5), large_ix_ids,
             large_peers, large_deps, ax, -30, 0)
    annotate('18', 'LINX L1', (-30, -30), large_ix_ids,
             large_peers, large_deps, ax, 0, -60)
    annotate('171', 'IX.br SP', (-45, -30), large_ix_ids,
             large_peers, large_deps, ax, 0, -20)
    xmin = ymin = 8e-1
    xmax = 3e3
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

    ax.set_ylim(ymin, ymax)
    # ax.yaxis.set_major_locator(ticker.MultipleLocator(0.2))
    # ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.1))
    ax.set_ylabel('#Dependent ASes')
    ax.set_yscale('log')

    ax.set_xlim(xmin, xmax)
    ax.set_xlabel('#Members')
    ax.set_xscale('log')

    ax.grid(False, 'minor', 'both')

    ax.legend(ncol=3, loc='lower center', bbox_to_anchor=(0.5, 1))

    plt.savefig(f'{output_dir}{output_file_prefix}{PLOT_FILE_SUFFIX}',
                bbox_inches='tight')
    plt.close()


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
    output_file_prefix = \
        f'{os.path.basename(input_file)[:-len(INPUT_FILE_SUFFIX)]}' \
        f'{OUTPUT_FILE_SUFFIX}'

    logging.info(f'Input file: {input_file}')
    logging.info(f'Output file: {output_file_prefix}')

    ixp_values = load_ixp_table(args.input_file)

    plot_scatter(ixp_values,
                 output_dir,
                 output_file_prefix)


if __name__ == '__main__':
    main()
    sys.exit(0)
