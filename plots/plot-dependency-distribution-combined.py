import argparse
import logging
import sys
from collections import defaultdict
from typing import Tuple

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

sys.path.append('../')
from tools.shared_functions import COLORS, read_to_set

DATA_DELIMITER = ','


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


def plot_dependency_cdf(ark_as_dependencies: dict,
                        ark_ixp_dependencies: dict,
                        atlas_as_dependencies: dict,
                        atlas_ixp_dependencies: dict,
                        output_file: str) -> None:
    ark_as_ids, ark_as_deps, ark_as_p = make_cdf(ark_as_dependencies)
    ark_ixp_ids, ark_ixp_deps, ark_ixp_p = make_cdf(ark_ixp_dependencies)
    atlas_as_ids, atlas_as_deps, atlas_as_p = make_cdf(atlas_as_dependencies)
    atlas_ixp_ids, atlas_ixp_deps, atlas_ixp_p = make_cdf(atlas_ixp_dependencies)

    fig, ax = plt.subplots()

    ax.plot(ark_as_deps,
            ark_as_p,
            color=COLORS['as'],
            label='AS (Ark)')
    ax.plot(ark_as_deps[-1],
            ark_as_p[-1],
            color=COLORS['as'],
            linestyle='',
            marker=2)

    ax.step(ark_ixp_deps,
            ark_ixp_p,
            color=COLORS['ixp'],
            label='IXP (Ark)')
    ax.plot(ark_ixp_deps[-1],
            ark_ixp_p[-1],
            color=COLORS['ixp'],
            linestyle='',
            marker=2)

    ax.plot(atlas_as_deps,
            atlas_as_p,
            color=COLORS['as'],
            label='AS (Atlas)',
            linestyle='--')
    ax.plot(atlas_as_deps[-1],
            atlas_as_p[-1],
            color=COLORS['as'],
            linestyle='',
            marker=2)

    ax.step(atlas_ixp_deps,
            atlas_ixp_p,
            color=COLORS['ixp'],
            label='IXP (Atlas)',
            linestyle='--')
    ax.plot(atlas_ixp_deps[-1],
            atlas_ixp_p[-1],
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

    ax.legend(ncol=4,
              loc='lower center',
              bbox_to_anchor=(0.5, 1),
              fontsize=12,
              columnspacing=1.3,
              handlelength=1.3)

    plt.savefig(output_file, bbox_inches='tight')
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('ark_hegemony')
    parser.add_argument('atlas_hegemony')
    parser.add_argument('valid_ixps')
    parser.add_argument('output_file')
    args = parser.parse_args()

    FORMAT = '%(asctime)s %(levelname)s %(message)s'
    logging.basicConfig(
        format=FORMAT,
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    ark_hegemony = args.ark_hegemony
    atlas_hegemony = args.atlas_hegemony
    valid_ixps_file = args.valid_ixps
    output_file = args.output_file

    logging.info(f'Ark input file: {ark_hegemony}')
    logging.info(f'Atlas input file: {atlas_hegemony}')
    logging.info(f'Output file: {output_file}')

    valid_ixps = read_to_set(valid_ixps_file)

    ark_as_dependencies, ark_ixp_dependencies = load_dependency_counts(ark_hegemony,
                                                                       hege_threshold=0.1,
                                                                       num_peers_threshold=10,
                                                                       valid_ixps=valid_ixps)
    atlas_as_dependencies, atlas_ixp_dependencies = load_dependency_counts(atlas_hegemony,
                                                                           hege_threshold=0.1,
                                                                           num_peers_threshold=10,
                                                                           valid_ixps=valid_ixps)

    plot_dependency_cdf(ark_as_dependencies,
                        ark_ixp_dependencies,
                        atlas_as_dependencies,
                        atlas_ixp_dependencies,
                        output_file)


if __name__ == '__main__':
    main()
    sys.exit(0)
