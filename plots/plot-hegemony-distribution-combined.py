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
from tools.shared_functions import COLORS, read_to_set

DATA_DELIMITER = ','

mpl.rcParams['xtick.major.pad'] = 6


def load_mean_hege(score_file: str,
                   hege_threshold: float = 0,
                   num_peers_threshold: int = 0,
                   valid_ixps: set = None) -> Tuple[dict, dict]:
    as_hege_lists = defaultdict(list)
    ixp_hege_lists = defaultdict(list)
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
                ixp_hege_lists[ix_id].append(hege)
            else:
                asn = asn.removeprefix('as|')
                as_hege_lists[asn].append(hege)
    as_mean_heges = {asn: np.mean(hege_list)
                     for asn, hege_list in as_hege_lists.items()}
    ixp_mean_heges = {ix_id: np.mean(hege_list)
                      for ix_id, hege_list in ixp_hege_lists.items()}
    logging.info(f'AS: {len(as_mean_heges)} IXP:{len(ixp_mean_heges)}')
    return as_mean_heges, ixp_mean_heges


def make_cdf(heges: dict) -> Tuple[list, np.ndarray, np.ndarray]:
    identifiers = list()
    mean_heges = list()
    for identifier, mean_hege in sorted(heges.items(), key=lambda t: t[1]):
        identifiers.append(identifier)
        mean_heges.append(mean_hege)
    p = np.arange(len(heges)) / (len(heges) - 1)
    return identifiers, np.array(mean_heges), p


def plot_hegemony_distribution(ark_as_mean_heges: dict,
                               ark_ixp_mean_heges: dict,
                               atlas_as_mean_heges: dict,
                               atlas_ixp_mean_heges: dict,
                               output_file: str) -> None:
    ark_as_ids, ark_as_heges, ark_as_p = make_cdf(ark_as_mean_heges)
    ark_ixp_ids, ark_ixp_heges, ark_ixp_p = make_cdf(ark_ixp_mean_heges)
    atlas_as_ids, atlas_as_heges, atlas_as_p = make_cdf(atlas_as_mean_heges)
    atlas_ixp_ids, atlas_ixp_heges, atlas_ixp_p = make_cdf(atlas_ixp_mean_heges)

    fig, ax = plt.subplots()

    ax.plot(ark_as_heges,
            ark_as_p,
            color=COLORS['as'],
            label='AS (Ark)')
    ax.plot(ark_ixp_heges,
            ark_ixp_p,
            color=COLORS['ixp'],
            label='IXP (Ark)')
    ax.plot(atlas_as_heges,
            atlas_as_p,
            color=COLORS['as'],
            label='AS (Atlas)',
            linestyle='--')
    ax.plot(atlas_ixp_heges,
            atlas_ixp_p,
            color=COLORS['ixp'],
            label='IXP (Atlas)',
            linestyle='--')

    ax.set_ylim(0, 1.05)
    ax.yaxis.set_major_locator(ticker.MultipleLocator(0.2))
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.1))
    ax.set_ylabel('CDF')

    ax.set_xlim(0, 1.05)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(0.2))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.1))
    ax.set_xlabel('Mean Hegemony Score')

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

    ark_as_mean_heges, ark_ixp_mean_heges = load_mean_hege(ark_hegemony,
                                                           hege_threshold=0.1,
                                                           num_peers_threshold=10,
                                                           valid_ixps=valid_ixps)
    atlas_as_mean_heges, atlas_ixp_mean_heges = load_mean_hege(atlas_hegemony,
                                                               hege_threshold=0.1,
                                                               num_peers_threshold=10,
                                                               valid_ixps=valid_ixps)
    plot_hegemony_distribution(ark_as_mean_heges,
                               ark_ixp_mean_heges,
                               atlas_as_mean_heges,
                               atlas_ixp_mean_heges,
                               output_file)


if __name__ == '__main__':
    main()
    sys.exit(0)
