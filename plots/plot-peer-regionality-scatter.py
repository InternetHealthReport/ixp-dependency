import argparse
import logging
import os
import sys
from re import I

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
OUTPUT_FILE_SUFFIX = '.pdb_regionality_scatter.pdf'
DATA_DELIMITER = ','

mpl.rcParams['legend.markerscale'] = 1.25
mpl.rcParams['legend.handletextpad'] = 0
mpl.rcParams['legend.columnspacing'] = 1
mpl.rcParams['axes.spines.right'] = True


def read_ixp_class(ixp_table_file: str) -> dict:
    ret = dict()
    with open(ixp_table_file, 'r') as f:
        f.readline()
        for line in f:
            line_split = line.strip().split(DATA_DELIMITER)
            ix_id = line_split[0]
            dependencies = int(line_split[12])
            if dependencies == 0:
                ret[ix_id] = 'no_deps'
            elif dependencies <= SMALL_IX_THRESHOLD:
                ret[ix_id] = 'small'
            elif dependencies <= MEDIUM_IX_THRESHOLD:
                ret[ix_id] = 'medium'
            else:
                ret[ix_id] = 'large'
    return ret


def load_pdb_regionality(input_file: str, ixp_class: dict) -> dict:
    ret = {'no_deps': list(),
           'small': list(),
           'medium': list(),
           'large': list()}
    with open(input_file, 'r') as f:
        f.readline()
        for line in f:
            line_split = line.strip().split(DATA_DELIMITER)
            ix_id = line_split[0]
            peers = int(line_split[1])
            if peers <= 1:
                continue
            regionality = float(line_split[2])
            ret[ixp_class[ix_id]].append((regionality, peers, ix_id))
    return ret


def plot_scatter(values: dict, ax: plt.Axes) -> None:
    no_deps_regionality, no_deps_peers, _ = zip(*values['no_deps'])
    if values['small']:
        small_regionality, small_peers, _ = zip(*values['small'])
    else:
        small_regionality = tuple()
        small_peers = tuple()
    if values['medium']:
        medium_regionality, medium_peers, _ = zip(*values['medium'])
    else:
        medium_regionality = tuple()
        medium_peers = tuple()
    if values['large']:
        large_regionality, large_peers, large_ix_ids = zip(*values['large'])
    else:
        large_regionality = tuple()
        large_peers = tuple()
        large_ix_ids = tuple()
    all_regionalities = no_deps_regionality + \
        small_regionality + medium_regionality + large_regionality

    ymin = 8e-1
    ymax = 3e3
    xmin = -0.05
    xmax = 1.05

    # We need to do an incredibly stupid switch here, so that the
    # histogram is drawn in the background...
    # You can change the layering within an axis using zorder, but
    # for two axes, the second one is always drawn last...
    ix_ax = ax.twinx()
    hist_ax = ax
    ix_ax.yaxis.tick_left()
    ix_ax.yaxis.set_label_position('left')
    ix_ax.grid(False, axis='x')
    hist_ax.yaxis.tick_right()
    hist_ax.yaxis.set_label_position('right')
    hist_ax.grid(False, axis='y')

    hist_ax.hist(all_regionalities,
             bins=21,
             range=(-0.025, 1.025),
             align='mid',
             alpha=0.4,
             color='#31a354')
    hist_ax.set_ylabel('#IXPs')

    ix_ax.plot(no_deps_regionality, no_deps_peers,
            linestyle='',
            marker=NO_DEPS_MARKER,
            color=COLORS['no_deps'],
            label='No deps.')
    ix_ax.plot(small_regionality, small_peers,
            linestyle='',
            marker=SMALL_IX_MARKER,
            color=COLORS['small'],
            label='Low')
    ix_ax.plot(medium_regionality, medium_peers,
            linestyle='',
            marker=MEDIUM_IX_MARKER,
            color=COLORS['medium'],
            label='Medium')
    ix_ax.plot(large_regionality, large_peers,
            linestyle='',
            marker=LARGE_IX_MARKER,
            color=COLORS['large'],
            label='High')

    annotate('31', 'DE-CIX Fr.', (10, 7), large_ix_ids,
             large_regionality, large_peers, ix_ax)
    annotate('26', 'AMS-IX', (-50, 14), large_ix_ids,
             large_regionality, large_peers, ix_ax, -0.005, 0)
    annotate('18', 'LINX L1', (20, -10), large_ix_ids,
             large_regionality, large_peers, ix_ax, 0.005, 0)
    annotate('171', 'IX.br SP', (-45, -25), large_ix_ids,
             large_regionality, large_peers, ix_ax, -0.005, -150)


    ix_ax.set_ylim(ymin, ymax)
    ix_ax.set_ylabel('#Members')
    ix_ax.set_yscale('log')
    ix_ax.grid(False, 'minor', 'y')

    ax.set_xlim(xmin, xmax)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(0.2))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.1))
    ax.set_xlabel('Regionality')


    ix_ax.legend(ncol=4, loc='lower center', bbox_to_anchor=(0.5, 1))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('ixp_table_file')
    parser.add_argument('ixp_pdb_regionality_file')
    parser.add_argument('output_dir')
    args = parser.parse_args()

    FORMAT = '%(asctime)s %(levelname)s %(message)s'
    logging.basicConfig(
        format=FORMAT,
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    ixp_table_file = args.ixp_table_file
    ixp_pdb_regionality_file = args.ixp_pdb_regionality_file
    output_dir = sanitize_dir(args.output_dir)
    output_file = f'{output_dir}' \
                  f'{os.path.basename(ixp_table_file)[:-len(INPUT_FILE_SUFFIX)]}' \
                  f'{OUTPUT_FILE_SUFFIX}'

    ixp_classes = read_ixp_class(ixp_table_file)
    regionality = load_pdb_regionality(ixp_pdb_regionality_file, ixp_classes)

    fig, ax = plt.subplots()
    plot_scatter(regionality, ax)

    plt.savefig(output_file, bbox_inches='tight')


if __name__ == '__main__':
    main()
    sys.exit(0)
