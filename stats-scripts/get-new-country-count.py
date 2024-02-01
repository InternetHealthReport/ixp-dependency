import argparse
import logging
import os
import sys
from collections import defaultdict
from typing import Tuple

from tools.shared_functions import sanitize_dir

sys.path.append('../')


INPUT_FILE_SUFFIX = '.per_as_ixp_dependencies.csv'
OUTPUT_FILE_SUFFIX = '.new_country_count.csv'
DATA_DELIMITER = ','
CC_INTERNATIONAL = '**'

DECIX_LG = '../stats/peeringdb/de-cix-fra-combined-member-asns.csv'
IXBR_LG = '../stats/peeringdb/ix-br-sp-combined-member-asns.csv'


def read_ixp_peers_file(input_file: str) -> Tuple[dict, dict, dict]:
    ixp_peer_count = defaultdict(int)
    ixp_cc = dict()
    ixp_peer_cc = defaultdict(set)
    with open(input_file, 'r') as f:
        f.readline()
        for line in f:
            line_split = line.strip().split(DATA_DELIMITER)
            ix_id = int(line_split[0])
            ix_cc = line_split[3]
            if ix_id not in ixp_cc:
                ixp_cc[ix_id] = ix_cc
            ixp_peer_count[ix_id] += 1
            peer_cc = line_split[4]
            if peer_cc == 'None' or peer_cc == CC_INTERNATIONAL:
                continue
            ixp_peer_cc[ix_id].add(peer_cc)
    return ixp_peer_count, ixp_cc, ixp_peer_cc


def read_per_as_ixp_dependencies_file(input_file: str) -> Tuple[dict, dict, dict]:
    ix_dep_count = dict()
    ix_dep_cc = defaultdict(set)
    ix_cc_dep = defaultdict(dict)
    with open(input_file, 'r') as f:
        f.readline()
        for line in f:
            line_split = line.strip().split(DATA_DELIMITER)
            cc = line_split[1]
            asn = line_split[2]
            if cc == CC_INTERNATIONAL or asn != 'general':
                continue
            ix_id = int(line_split[0])
            dependencies = int(line_split[3])
            if cc == 'overview':
                ix_dep_count[ix_id] = dependencies
                continue
            ix_dep_cc[ix_id].add(cc)
            ix_cc_dep[ix_id][cc] = dependencies
    return ix_dep_count, ix_dep_cc, ix_cc_dep


def read_lg_member_asns(input_file: str) -> Tuple[int, set]:
    peer_count = 0
    peer_cc = set()
    with open(input_file, 'r') as f:
        f.readline()
        for line in f:
            peer_count += 1
            peer_cc.add(line.strip().split(DATA_DELIMITER)[1])
    if CC_INTERNATIONAL in peer_cc:
        peer_cc.remove(CC_INTERNATIONAL)
    return peer_count, peer_cc


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('ixp_peers_file')
    parser.add_argument('per_as_ixp_dependencies_file')
    parser.add_argument('output_dir')
    args = parser.parse_args()

    FORMAT = '%(asctime)s %(levelname)s %(message)s'
    logging.basicConfig(
        format=FORMAT,
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    ixp_peers_file = args.ixp_peers_file
    per_as_dependencies_file = args.per_as_ixp_dependencies_file

    lg_asns = {31: read_lg_member_asns(DECIX_LG),
               171: read_lg_member_asns(IXBR_LG)}

    output_dir = sanitize_dir(args.output_dir)
    output_file_prefix = \
        os.path.basename(per_as_dependencies_file)[:-len(INPUT_FILE_SUFFIX)]
    output_file = f'{output_dir}{output_file_prefix}{OUTPUT_FILE_SUFFIX}'

    ixp_peer_count, ixp_cc, ixp_peer_countries = \
        read_ixp_peers_file(ixp_peers_file)
    ixp_dep_count, ixp_dep_countries, ixp_countries_dep = \
        read_per_as_ixp_dependencies_file(per_as_dependencies_file)

    with open(output_file, 'w') as f:
        headers = ('ix_id', 'cc', 'num_peers', 'peer_countries', 'num_deps', 'num_deps_dep_no_peer',
                   'dependency_countries', 'both', 'peer_no_dep',
                   'dep_no_peer')
        f.write(DATA_DELIMITER.join(headers) + '\n')
        for ix_id in sorted(ixp_cc):
            ix_cc = ixp_cc[ix_id]
            num_peers = ixp_peer_count[ix_id]
            peer_cc = ixp_peer_countries[ix_id]
            if ix_id in lg_asns:
                num_peers = lg_asns[ix_id][0]
                peer_cc = lg_asns[ix_id][1]
            peer_countries = len(peer_cc)
            num_deps = 0
            num_deps_dep_no_peer = 0
            dependency_countries = 0
            both = 0
            peer_no_dep = peer_countries
            dep_no_peer = 0
            if ix_id in ixp_dep_count:
                num_deps = ixp_dep_count[ix_id]
                dep_cc = ixp_dep_countries[ix_id]
                dependency_countries = len(dep_cc)
                both = len(peer_cc.intersection(dep_cc))
                peer_no_dep = len(peer_cc - dep_cc)
                dep_no_peer_set = dep_cc - peer_cc
                dep_no_peer = len(dep_no_peer_set)
                for cc in dep_no_peer_set:
                    if cc in ixp_countries_dep[ix_id]:
                        num_deps_dep_no_peer += ixp_countries_dep[ix_id][cc]
            line = (ix_id, ix_cc, num_peers, peer_countries, num_deps, num_deps_dep_no_peer,
                    dependency_countries, both, peer_no_dep, dep_no_peer)
            f.write(DATA_DELIMITER.join(map(str, line)) + '\n')


if __name__ == '__main__':
    main()
    sys.exit(0)
