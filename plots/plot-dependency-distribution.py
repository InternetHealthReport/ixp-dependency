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
from tools.shared_functions import COLORS, annotate, read_to_set, sanitize_dir

INPUT_FILE_SUFFIX = '.hegemony.csv'
OUTPUT_FILE_SUFFIX_CDF = '.dependencies_cdf'
OUTPUT_FILE_SUFFIX_CCDF = '.dependencies_ccdf'
PLOT_FILE_SUFFIX = '.pdf'
STAT_FILE_SUFFIX = '.csv'
DATA_DELIMITER = ','

mpl.rcParams['legend.markerscale'] = 1.25


def load_dependency_counts(score_file: str,
                           hege_threshold: float = 0,
                           num_peers_threshold: int = 0,
                           valid_ixps: set = None) -> Tuple[dict, dict]:
    as_dependencies = defaultdict(int)
    ixp_dependencies = defaultdict(int)
    with open(score_file, 'r') as f:
        f.readline()
        for line in f:
            line_split = line.strip().split(DATA_DELIMITER)
            scope = line_split[0]
            asn = line_split[1]
            hege = float(line_split[2])
            num_peers = int(line_split[3])
            if (hege < hege_threshold
                    or num_peers < num_peers_threshold
                    or scope == asn
                    or scope == '-1'
                    or 'ip' in line
                    or ';' in asn
                    or hege > 1):
                continue
            if asn.startswith('ix|'):
                ix_id = asn.removeprefix('ix|')
                if valid_ixps and ix_id not in valid_ixps:
                    continue
                ixp_dependencies[ix_id] += 1
            else:
                asn = asn.removeprefix('as|')
                as_dependencies[asn] += 1
    return as_dependencies, ixp_dependencies


def make_cdf(dependencies: dict) -> Tuple[list, np.ndarray, np.ndarray]:
    identifiers = list()
    dep_counts = list()
    for identifier, num_deps in sorted(dependencies.items(), key=lambda t: t[1]):
        identifiers.append(identifier)
        dep_counts.append(num_deps)
    p = np.arange(len(dependencies)) / (len(dependencies) - 1)
    return identifiers, np.array(dep_counts), p


def make_ccdf(dependencies: dict) -> Tuple[list, np.ndarray, np.ndarray]:
    identifiers = list()
    dep_counts = list()
    for identifier, num_deps in sorted(dependencies.items(), key=lambda t: t[1]):
        identifiers.append(identifier)
        dep_counts.append(num_deps)
    p = np.arange(len(dependencies)) / len(dependencies)
    p = 1 - p
    return identifiers, np.array(dep_counts), p


def plot_dependency_ccdf(as_dependencies: dict,
                         ixp_dependencies: dict,
                         output_dir: str,
                         output_file_prefix: str) -> None:
    as_ids, as_deps, as_p = make_ccdf(as_dependencies)
    ixp_ids, ixp_deps, ixp_p = make_ccdf(ixp_dependencies)

    fig, ax = plt.subplots()

    ax.plot(as_deps,
            as_p,
            color=COLORS['as'],
            label='AS',
            linestyle='',
            marker='x')
    if 'ark' in output_file_prefix:
        annotate('3356', 'Level 3', (-15, 20), as_ids, as_deps, as_p, ax, 0, 1e-5)
        annotate('1299', 'Arelion', (-30, 20), as_ids, as_deps, as_p, ax, 0, 3e-5)
        annotate('174', 'Cogent', (-30, 20), as_ids, as_deps, as_p, ax, 0, 4e-5)
        annotate('6939', 'Hurricane Electric', (-55, -30), as_ids, as_deps, as_p, ax, 0, -5e-5)

        annotate('31', 'DE-CIX Frankfurt', (20, -10), ixp_ids, ixp_deps, ixp_p, ax)
        annotate('26', 'AMS-IX', (20, -10), ixp_ids, ixp_deps, ixp_p, ax)
        annotate('18', 'LINX LON1', (20, 0), ixp_ids, ixp_deps, ixp_p, ax)
        annotate('1', 'Equinix Ashburn', (5, 20), ixp_ids, ixp_deps, ixp_p, ax, 100, 0)
    elif 'traceroutev4' in output_file_prefix:
        annotate('3356', 'Level 3', (-15, 20), as_ids, as_deps, as_p, ax, 0, 1e-5)
        annotate('1299', 'Arelion', (-10, 15), as_ids, as_deps, as_p, ax, 0, 3e-5)
        annotate('174', 'Cogent', (-25, -30), as_ids, as_deps, as_p, ax, 0, 1e-5)
        annotate('6939', 'Hurricane Electric', (-70, 17), as_ids, as_deps, as_p, ax, 0, 1e-5)

        annotate('31', 'DE-CIX Frankfurt', (20, -10), ixp_ids, ixp_deps, ixp_p, ax)
        annotate('26', 'AMS-IX', (20, 0), ixp_ids, ixp_deps, ixp_p, ax)
        annotate('18', 'LINX LON1', (20, -5), ixp_ids, ixp_deps, ixp_p, ax)
        annotate('1', 'Equinix Ashburn', (5, 20), ixp_ids, ixp_deps, ixp_p, ax, 100, 0)


    ax.plot(ixp_deps,
            ixp_p,
            color=COLORS['ixp'],
            label='IXP',
            linestyle='',
            marker='1')

    ax.set_ylim(ymin=1e-4)
    ax.set_yscale('log')
    ax.set_ylabel('CCDF')

    # ax.set_xscale('log')
    ax.set_xlim(-1e3, 3.25e4)
    ax.set_xlabel('#Dependent ASes')
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(2500))
    ax.xaxis.set_major_locator(ticker.MultipleLocator(5000))
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f'{int(x / 1000)}k'))

    ax.grid(False, 'minor', 'y')

    ax.legend(ncol=2, loc='lower center', bbox_to_anchor=(0.5, 1))

    plt.savefig(f'{output_dir}{output_file_prefix}{PLOT_FILE_SUFFIX}', bbox_inches='tight')
    plt.close()


def plot_dependency_cdf(as_dependencies: dict,
                        ixp_dependencies: dict,
                        output_dir: str,
                        output_file_prefix: str) -> None:
    as_ids, as_deps, as_p = make_cdf(as_dependencies)
    ixp_ids, ixp_deps, ixp_p = make_cdf(ixp_dependencies)

    fig, ax = plt.subplots()

    ax.plot(as_deps,
            as_p,
            color=COLORS['as'],
            label='AS')
    if len(as_deps) > 0:
        ax.plot(as_deps[-1],
                as_p[-1],
                color=COLORS['as'],
                linestyle='',
                marker=2)

    ax.step(ixp_deps,
            ixp_p,
            color=COLORS['ixp'],
            label='IXP')
    if len(ixp_deps) > 0:
        ax.plot(ixp_deps[-1],
                ixp_p[-1],
                color=COLORS['ixp'],
                linestyle='',
                marker=2)

    ax.set_ylim(0, 1.05)
    ax.yaxis.set_major_locator(ticker.MultipleLocator(0.2))
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.1))
    ax.set_ylabel('CDF')

    ax.set_xscale('log')
    ax.set_xlim(8e-1, 5e4)
    ax.set_xlabel('#Dependent ASes')
    ax.grid(False, 'minor', 'x')

    ax.legend(ncol=2, loc='lower center', bbox_to_anchor=(0.5, 1))

    plt.savefig(f'{output_dir}{output_file_prefix}{PLOT_FILE_SUFFIX}', bbox_inches='tight')
    plt.close()
    with open(f'{output_dir}fig-stats/{output_file_prefix}.as{STAT_FILE_SUFFIX}', 'w') as f:
        headers = ('p', 'dependencies', 'identifier')
        f.write(DATA_DELIMITER.join(headers) + '\n')
        for idx in range(len(as_p)):
            line = (as_p[idx], as_deps[idx], as_ids[idx])
            f.write(DATA_DELIMITER.join(map(str, line)) + '\n')
    with open(f'{output_dir}fig-stats/{output_file_prefix}.ixp{STAT_FILE_SUFFIX}', 'w') as f:
        headers = ('p', 'dependencies', 'identifier')
        f.write(DATA_DELIMITER.join(headers) + '\n')
        for idx in range(len(ixp_p)):
            line = (ixp_p[idx], ixp_deps[idx], ixp_ids[idx])
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
    output_file_prefix_cdf = \
        f'{os.path.basename(input_file)[:-len(INPUT_FILE_SUFFIX)]}' \
        f'{OUTPUT_FILE_SUFFIX_CDF}'
    output_file_prefix_ccdf = \
        f'{os.path.basename(input_file)[:-len(INPUT_FILE_SUFFIX)]}' \
        f'{OUTPUT_FILE_SUFFIX_CCDF}'

    logging.info(f'Input file: {input_file}')
    logging.info(f'Output file CDF: {output_file_prefix_cdf}')
    logging.info(f'Output file CCDF: {output_file_prefix_ccdf}')

    valid_ixps = read_to_set(valid_ixps_file)

    as_dependencies, ixp_dependencies = \
        load_dependency_counts(input_file,
                               hege_threshold=0.1,
                               num_peers_threshold=10,
                               valid_ixps=valid_ixps)

    plot_dependency_cdf(as_dependencies,
                        ixp_dependencies,
                        output_dir,
                        output_file_prefix_cdf)
    plot_dependency_ccdf(as_dependencies,
                         ixp_dependencies,
                         output_dir,
                         output_file_prefix_ccdf)


if __name__ == '__main__':
    main()
    sys.exit(0)
