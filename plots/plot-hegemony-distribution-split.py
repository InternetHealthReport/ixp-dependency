import argparse
import logging
import os
import sys
from collections import defaultdict
from typing import Tuple

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

sys.path.append('../')
from tools.shared_functions import (COLORS, MEDIUM_AS_THRESHOLD,
                                    MEDIUM_IX_THRESHOLD, SMALL_AS_THRESHOLD,
                                    SMALL_IX_THRESHOLD, read_to_set,
                                    sanitize_dir)

INPUT_FILE_SUFFIX = '.hegemony.csv'
OUTPUT_FILE_SUFFIX = '.hegemony_split_cdf'
PLOT_FILE_SUFFIX = '.pdf'
STAT_FILE_SUFFIX = '.csv'
DATA_DELIMITER = ','


mpl.rcParams['xtick.major.pad'] = 6


def three_way_split(data: dict, thresh_1: int, thresh_2: int) -> Tuple[dict, dict, dict]:
    small_mean_heges = dict()
    medium_mean_heges = dict()
    large_mean_heges = dict()
    for identifier, hege_list in data.items():
        dep_count = len(hege_list)
        mean_hege = np.mean(hege_list)
        if dep_count <= thresh_1:
            small_mean_heges[identifier] = mean_hege
        elif dep_count <= thresh_2:
            medium_mean_heges[identifier] = mean_hege
        else:
            large_mean_heges[identifier] = mean_hege
    return small_mean_heges, medium_mean_heges, large_mean_heges


def load_split_mean_hege(score_file: str,
                         hege_threshold: float = 0,
                         num_peers_threshold: int = 0,
                         valid_ixps: set = None) -> Tuple[dict, dict]:
    as_hege_lists = defaultdict(list)
    ix_hege_lists = defaultdict(list)
    with open(score_file, 'r') as f:
        f.readline()
        for line in f:
            line_split = line.strip().split(DATA_DELIMITER)
            scope = line_split[0]
            asn = line_split[1]
            hege = float(line_split[2])
            num_peers = int(line_split[3])
            if hege < hege_threshold \
                    or num_peers < num_peers_threshold \
                    or 'ip' in line \
                    or scope == asn \
                    or scope == '-1' \
                    or ';' in asn \
                    or hege > 1:
                continue
            if asn.startswith('ix|'):
                ix_id = asn.removeprefix('ix|')
                if valid_ixps and ix_id not in valid_ixps:
                    continue
                ix_hege_lists[ix_id].append(hege)
            else:
                asn = asn.removeprefix('as|')
                as_hege_lists[asn].append(hege)
    small_as_mean_heges, medium_as_mean_heges, large_as_mean_heges = three_way_split(
        as_hege_lists, SMALL_AS_THRESHOLD, MEDIUM_AS_THRESHOLD)
    small_ix_mean_heges, medium_ix_mean_heges, large_ix_mean_heges = three_way_split(
        ix_hege_lists, SMALL_IX_THRESHOLD, MEDIUM_IX_THRESHOLD)
    print(
        f'AS small:{len(small_as_mean_heges)} medium:{len(medium_as_mean_heges)} large:{len(large_as_mean_heges)}')
    print(
        f'IX small:{len(small_ix_mean_heges)} medium:{len(medium_ix_mean_heges)} large:{len(large_ix_mean_heges)}')
    return small_as_mean_heges, medium_as_mean_heges, large_as_mean_heges, small_ix_mean_heges, medium_ix_mean_heges, large_ix_mean_heges


def make_cdf(heges: dict) -> Tuple[list, np.ndarray, np.ndarray]:
    identifiers = list()
    mean_heges = list()
    for identifier, mean_hege in sorted(heges.items(), key=lambda t: t[1]):
        identifiers.append(identifier)
        mean_heges.append(mean_hege)
    p = np.arange(len(heges)) / (len(heges) - 1)
    return identifiers, np.array(mean_heges), p


def plot_dependency_distribution(small_as_mean_heges: dict,
                                 medium_as_mean_heges: dict,
                                 large_as_mean_heges: dict,
                                 small_ix_mean_heges: dict,
                                 medium_ix_mean_heges: dict,
                                 large_ix_mean_heges: dict,
                                 output_dir: str,
                                 output_file_prefix: str) -> None:
    small_as_ids, small_as_heges, small_as_p = make_cdf(small_as_mean_heges)
    medium_as_ids, medium_as_heges, medium_as_p = make_cdf(
        medium_as_mean_heges)
    large_as_ids, large_as_heges, large_as_p = make_cdf(large_as_mean_heges)
    small_ix_ids, small_ix_heges, small_ix_p = make_cdf(small_ix_mean_heges)
    medium_ix_ids, medium_ix_heges, medium_ix_p = make_cdf(
        medium_ix_mean_heges)
    large_ix_ids, large_ix_heges, large_ix_p = make_cdf(large_ix_mean_heges)

    fig, ax = plt.subplots()

    ax.plot(small_as_heges,
            small_as_p,
            color=COLORS['as'],
            label=f'Low AS',
            linestyle=':')

    ax.step(small_ix_heges,
            small_ix_p,
            color=COLORS['ixp'],
            label=f'Low IXP',
            linestyle=':')

    ax.plot(medium_as_heges,
            medium_as_p,
            color=COLORS['as'],
            label=f'Medium AS',
            linestyle='-.')

    ax.step(medium_ix_heges,
            medium_ix_p,
            color=COLORS['ixp'],
            label=f'Medium IXP',
            linestyle='-.')

    ax.step(large_as_heges,
            large_as_p,
            color=COLORS['as'],
            label=f'High AS')

    ax.step(large_ix_heges,
            large_ix_p,
            color=COLORS['ixp'],
            label=f'High IXP')

    ax.set_ylim(0, 1.05)
    ax.yaxis.set_major_locator(ticker.MultipleLocator(0.2))
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.1))
    ax.set_ylabel('CDF')

    ax.set_xlim(0, 1.05)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(0.2))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.1))
    ax.set_xlabel('Mean Hegemony Score')

    ax.legend(ncol=3, loc='lower center', bbox_to_anchor=(0.5, 1), fontsize=13)

    plt.savefig(
        f'{output_dir}{output_file_prefix}{PLOT_FILE_SUFFIX}', bbox_inches='tight')
    plt.close()
    with open(f'{output_dir}fig-stats/{output_file_prefix}.small_as{STAT_FILE_SUFFIX}', 'w') as f:
        headers = ('p', 'mean_hege', 'identifier')
        f.write(DATA_DELIMITER.join(headers) + '\n')
        for idx in range(len(small_as_p)):
            line = (small_as_p[idx], small_as_heges[idx], small_as_ids[idx])
            f.write(DATA_DELIMITER.join(map(str, line)) + '\n')
    with open(f'{output_dir}fig-stats/{output_file_prefix}.medium_as{STAT_FILE_SUFFIX}', 'w') as f:
        headers = ('p', 'mean_hege', 'identifier')
        f.write(DATA_DELIMITER.join(headers) + '\n')
        for idx in range(len(medium_as_p)):
            line = (medium_as_p[idx], medium_as_heges[idx], medium_as_ids[idx])
            f.write(DATA_DELIMITER.join(map(str, line)) + '\n')
    with open(f'{output_dir}fig-stats/{output_file_prefix}.large_as{STAT_FILE_SUFFIX}', 'w') as f:
        headers = ('p', 'mean_hege', 'identifier')
        f.write(DATA_DELIMITER.join(headers) + '\n')
        for idx in range(len(large_as_p)):
            line = (large_as_p[idx], large_as_heges[idx], large_as_ids[idx])
            f.write(DATA_DELIMITER.join(map(str, line)) + '\n')
    with open(f'{output_dir}fig-stats/{output_file_prefix}.small_ixp{STAT_FILE_SUFFIX}', 'w') as f:
        headers = ('p', 'mean_hege', 'identifier')
        f.write(DATA_DELIMITER.join(headers) + '\n')
        for idx in range(len(small_ix_p)):
            line = (small_ix_p[idx], small_ix_heges[idx], small_ix_ids[idx])
            f.write(DATA_DELIMITER.join(map(str, line)) + '\n')
    with open(f'{output_dir}fig-stats/{output_file_prefix}.medium_ixp{STAT_FILE_SUFFIX}', 'w') as f:
        headers = ('p', 'mean_hege', 'identifier')
        f.write(DATA_DELIMITER.join(headers) + '\n')
        for idx in range(len(medium_ix_p)):
            line = (medium_ix_p[idx], medium_ix_heges[idx], medium_ix_ids[idx])
            f.write(DATA_DELIMITER.join(map(str, line)) + '\n')
    with open(f'{output_dir}fig-stats/{output_file_prefix}.large_ixp{STAT_FILE_SUFFIX}', 'w') as f:
        headers = ('p', 'mean_hege', 'identifier')
        f.write(DATA_DELIMITER.join(headers) + '\n')
        for idx in range(len(large_ix_p)):
            line = (large_ix_p[idx], large_ix_heges[idx], large_ix_ids[idx])
            f.write(DATA_DELIMITER.join(map(str, line)) + '\n')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('input_hegemony_file')
    parser.add_argument('valid_ixps')
    parser.add_argument('output_dir')
    args = parser.parse_args()

    FORMAT = '%(asctime)s %(levelname)s %(message)s'
    logging.basicConfig(
        format=FORMAT,
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    input_file = args.input_hegemony_file
    valid_ixps_file = args.valid_ixps
    output_dir = sanitize_dir(args.output_dir)
    output_file_prefix = \
        f'{os.path.basename(input_file)[:-len(INPUT_FILE_SUFFIX)]}' \
        f'{OUTPUT_FILE_SUFFIX}'

    logging.info(f'Input file: {input_file}')
    logging.info(f'Output file: {output_file_prefix}')

    valid_ixps = read_to_set(valid_ixps_file)

    small_as_mean_heges, medium_as_mean_heges, large_as_mean_heges, \
        small_ix_mean_heges, medium_ix_mean_heges, large_ix_mean_heges = \
        load_split_mean_hege(input_file, hege_threshold=0.1,
                             num_peers_threshold=10,
                             valid_ixps=valid_ixps)

    plot_dependency_distribution(small_as_mean_heges,
                                 medium_as_mean_heges,
                                 large_as_mean_heges,
                                 small_ix_mean_heges,
                                 medium_ix_mean_heges,
                                 large_ix_mean_heges,
                                 output_dir,
                                 output_file_prefix)


if __name__ == '__main__':
    main()
    sys.exit(0)
