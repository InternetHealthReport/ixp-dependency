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
from tools.shared_functions import (COLORS, LARGE_IX_MARKER, MEDIUM_IX_MARKER,
                                    MEDIUM_IX_THRESHOLD, NO_DEPS_MARKER,
                                    SMALL_IX_MARKER, SMALL_IX_THRESHOLD,
                                    annotate, sanitize_dir)

INPUT_FILE_SUFFIX = '.ixp_table.csv'
OUTPUT_FILE_SUFFIX = '.ixp_peer_seen_scatter'
PLOT_FILE_SUFFIX = '.pdf'
STAT_FILE_SUFFIX = '.csv'
DATA_DELIMITER = ','

mpl.rcParams['legend.markerscale'] = 1.25
mpl.rcParams['legend.handletextpad'] = 0
mpl.rcParams['legend.columnspacing'] = 1


def load_ixp_table(ixp_table_files) -> Tuple[list, list, list, list]:
    no_deps = list()
    small = list()
    medium = list()
    large = list()
    with open(ixp_table_files, 'r') as f:
        f.readline()
        for line in f:
            line_split = line.strip().split(DATA_DELIMITER)
            peers = int(line_split[5])
            if peers <= 1:
                continue
            dependencies = int(line_split[12])
            peers_seen_r = float(line_split[20])
            if peers_seen_r == 0:
                continue
            ix_id = line_split[0]
            value = (peers, peers_seen_r, dependencies, ix_id)
            if dependencies == 0:
                no_deps.append(value)
            elif dependencies <= SMALL_IX_THRESHOLD:
                small.append(value)
            elif dependencies <= MEDIUM_IX_THRESHOLD:
                medium.append(value)
            else:
                large.append(value)
    return no_deps, small, medium, large


def compute_stats(values: list) -> Tuple[float, float]:
    error = np.std(values) / np.sqrt(len(values))
    return np.mean(values), error


def plot_scatter(ixp_values: Tuple[list, list, list, list],
                 output_dir: str,
                 output_file_prefix: str) -> None:

    no_deps_peers, no_deps_peers_seen_r, _, _ = zip(*ixp_values[0])
    small_peers, small_peers_seen_r, _, _ = zip(*ixp_values[1])
    medium_peers, medium_peers_seen_r, _, _ = zip(*ixp_values[2])
    large_peers, large_peers_seen_r, _, large_ix_ids = zip(*ixp_values[3])

    fig, ax = plt.subplots()

    ax.plot(no_deps_peers,
            no_deps_peers_seen_r,
            color=COLORS['no_deps'],
            label=f'No deps.',
            linestyle='',
            marker=NO_DEPS_MARKER)
    ax.plot(small_peers,
            small_peers_seen_r,
            color=COLORS['small'],
            label=f'Low',
            linestyle='',
            marker=SMALL_IX_MARKER)
    ax.plot(medium_peers,
            medium_peers_seen_r,
            color=COLORS['medium'],
            label=f'Medium',
            linestyle='',
            marker=MEDIUM_IX_MARKER)
    ax.plot(large_peers,
            large_peers_seen_r,
            color=COLORS['large'],
            label=f'High',
            linestyle='',
            marker=LARGE_IX_MARKER)
    annotate('31', 'DE-CIX Fr.', (-35, 30), large_ix_ids,
             large_peers, large_peers_seen_r, ax, 0, 0.01)
    annotate('26', 'AMS-IX', (-80, 10), large_ix_ids,
             large_peers, large_peers_seen_r, ax)
    annotate('18', 'LINX L1', (-70, -5), large_ix_ids,
             large_peers, large_peers_seen_r, ax, -50, 0)
    annotate('171', 'IX.br SP', (-45, -30), large_ix_ids,
             large_peers, large_peers_seen_r, ax, 0, -0.01)
    # nd_x, nd_xerr = compute_stats(no_deps_peers)
    # nd_y, nd_yerr = compute_stats(no_deps_peers_seen_r)
    # ax.errorbar(nd_x, nd_y, xerr=nd_xerr, yerr=nd_yerr, marker=NO_DEPS_MARKER, color=COLORS['centroid'], capsize=1)
    # sp_x, sp_xerr = compute_stats(small_peers)
    # sp_y, sp_yerr = compute_stats(small_peers_seen_r)
    # ax.errorbar(sp_x, sp_y, xerr=sp_xerr, yerr=sp_yerr, marker=SMALL_IX_MARKER, color=COLORS['centroid'], capsize=1)
    # mp_x, mp_xerr = compute_stats(medium_peers)
    # mp_y, mp_yerr = compute_stats(medium_peers_seen_r)
    # ax.errorbar(mp_x, mp_y, xerr=mp_xerr, yerr=mp_yerr, marker=MEDIUM_IX_MARKER, color=COLORS['centroid'], capsize=1)
    # lp_x, lp_xerr = compute_stats(large_peers)
    # lp_y, lp_yerr = compute_stats(large_peers_seen_r)
    # ax.errorbar(lp_x, lp_y, xerr=lp_xerr, yerr=lp_yerr, marker=LARGE_IX_MARKER, color=COLORS['centroid'], capsize=1)

    ax.set_ylim(-0.025, 1.05)
    ax.yaxis.set_major_locator(ticker.MultipleLocator(0.2))
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.1))
    ax.set_ylabel('Fraction of Members Seen in Traceroute')

    ax.set_xlim(8e-1, 3e3)
    ax.set_xlabel('#Members')
    ax.set_xscale('log')
    ax.grid(False, 'minor', 'x')

    ax.legend(ncol=4, loc='lower center', bbox_to_anchor=(0.5, 1))

    plt.savefig(f'{output_dir}{output_file_prefix}{PLOT_FILE_SUFFIX}',
                bbox_inches='tight')
    plt.close()
    with open(f'{output_dir}fig-stats/{output_file_prefix}{STAT_FILE_SUFFIX}', 'w') as f:
        headers = ('peers', 'peers_seen_r', 'dependencies', 'ix_id')
        f.write(DATA_DELIMITER.join(headers) + '\n')
        for peers in ixp_values:
            for value in sorted(peers):
                f.write(DATA_DELIMITER.join(map(str, value)) + '\n')

    with open(f'{output_dir}fig-stats/{output_file_prefix}.small_ixp{STAT_FILE_SUFFIX}', 'w') as f:
        headers = ('peers', 'peers_seen_r', 'dependencies', 'ix_id')
        f.write(DATA_DELIMITER.join(headers) + '\n')
        for value in sorted(ixp_values[1]):
            f.write(DATA_DELIMITER.join(map(str, value)) + '\n')
    with open(f'{output_dir}fig-stats/{output_file_prefix}.medium_ixp{STAT_FILE_SUFFIX}', 'w') as f:
        headers = ('peers', 'peers_seen_r', 'dependencies', 'ix_id')
        f.write(DATA_DELIMITER.join(headers) + '\n')
        for value in sorted(ixp_values[2]):
            f.write(DATA_DELIMITER.join(map(str, value)) + '\n')
    with open(f'{output_dir}fig-stats/{output_file_prefix}.large_ixp{STAT_FILE_SUFFIX}', 'w') as f:
        headers = ('peers', 'peers_seen_r', 'dependencies', 'ix_id')
        f.write(DATA_DELIMITER.join(headers) + '\n')
        for value in sorted(ixp_values[3]):
            f.write(DATA_DELIMITER.join(map(str, value)) + '\n')


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
