import argparse
import logging
import os
import sys
from collections import defaultdict, namedtuple
from typing import Tuple

sys.path.append('../')
from tools.shared_functions import sanitize_dir

Ixp = namedtuple('Ixp', 'id org_id name name_long cc peers')

HEGEMONY_FILE_SUFFIX = '.hegemony.csv'
OUTPUT_FILE_SUFFIX = '.ixp_table.csv'
DATA_DELIMITER = ','

DECIX_LG = '../raw-data/lg-dumps/de-cix-fra-member-asns.csv'
IXBR_LG = '../raw-data/lg-dumps/ix-br-sp-member-asns.csv'
LINX_LG = '../raw-data/lg-dumps/linx-lon1-member-asns.csv'


def read_ixp_file(ixp_file: str) -> dict:
    ret = dict()
    logging.info(f'Reading IXP data from {ixp_file}')
    with open(ixp_file, 'r') as f:
        f.readline()
        for line in f:
            line_split = line.strip().split(DATA_DELIMITER)
            ix_id = line_split[0]
            org_id = line_split[1]
            name = line_split[2]
            name_long = line_split[3]
            cc = line_split[4]
            peers = int(line_split[6])  # IPv4 peers
            ret[ix_id] = Ixp(ix_id, org_id, name, name_long, cc, peers)
    logging.info(f'Read {len(ret)} IXP entries.')
    return ret


def read_ixp_peers_file(ixp_peers_file: str) -> dict:
    ret = defaultdict(dict)
    logging.info(f'Reading IXP peers from {ixp_peers_file}')
    with open(ixp_peers_file, 'r') as f:
        f.readline()
        for line in f:
            line_split = line.strip().split(DATA_DELIMITER)
            ix_id = line_split[0]
            peer_asn = line_split[2]
            if line_split[5] == 'True':
                national = True
            elif line_split[5] == 'False':
                national = False
            else:
                national = None
            ret[ix_id][peer_asn] = national
    return ret


def read_interfaces_file(interfaces_file: str) -> dict:
    ret = defaultdict(lambda: {'peer_asn': set(),
                               'interfaces': 0,
                               'tr_count': 0})
    logging.info(f'Reading interfaces from {interfaces_file}')
    with open(interfaces_file, 'r') as f:
        f.readline()
        for line in f:
            line_split = line.split(DATA_DELIMITER)
            ix_id = line_split[0]
            asn = line_split[1]
            count = int(line_split[3])
            if asn != '0':
                ret[ix_id]['peer_asn'].add(asn)
            # The interfaces file contains one line per interface,
            # which are unique, so we can just increment per line.
            ret[ix_id]['interfaces'] += 1
            ret[ix_id]['tr_count'] += count
    return ret


def read_hegemony_file(hegemony_file: str,
                       min_hegemony_threshold: float,
                       min_peer_threshold: int) -> dict:
    ret = defaultdict(set)
    logging.info(f'Reading hegemony scores from {hegemony_file}')
    with open(hegemony_file, 'r') as f:
        f.readline()
        for line in f:
            line_split = line.strip().split(DATA_DELIMITER)
            scope = line_split[0]
            asn = line_split[1]
            hegemony = float(line_split[2])
            nb_peers = int(line_split[3])
            if (not asn.startswith('ix|')
                or not scope.startswith('as|')
                    or hegemony < min_hegemony_threshold
                    or nb_peers < min_peer_threshold
                    or 'ip' in line
                    or ';' in asn
                    or hegemony > 1):
                continue
            ix_id = asn.removeprefix('ix|')
            ret[ix_id].add(scope.removeprefix('as|'))
    return ret


def read_asn_country_map(asn_cc_map: str) -> dict:
    ret = dict()
    with open(asn_cc_map, 'r') as f:
        f.readline()
        for line in f:
            asn, count, cc = line.strip().split(DATA_DELIMITER)
            if int(count) > 1:
                cc = '**'
            ret[asn] = cc
    return ret


def read_lg_member_asns(input_file: str) -> set:
    with open(input_file, 'r') as f:
        return {l.strip() for l in f}


def count_national_peers(peers: dict) -> Tuple[int, int, int]:
    national = 0
    international = 0
    unknown = 0
    for value in peers.values():
        if value is True:
            national += 1
        elif value is False:
            international += 1
        elif value is None:
            unknown += 1
        else:
            logging.critical('Wat')
            sys.exit(1)
    return national, international, unknown


def map_national(ixp_cc: str,
                 dependencies: set,
                 asn_cc: dict) -> Tuple[int, int, int]:
    national = 0
    international = 0
    unknown = 0
    for asn in dependencies:
        if asn not in asn_cc:
            unknown += 1
            continue
        if asn_cc[asn] == ixp_cc:
            national += 1
        else:
            international += 1
    return national, international, unknown


def check_missing_files(file_list: list) -> bool:
    for file in file_list:
        if not os.path.exists(file):
            logging.error(f'File missing: {file}')
            return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('ixp_file')
    parser.add_argument('ixp_peers_file')
    parser.add_argument('interfaces_file')
    parser.add_argument('hegemony_file')
    parser.add_argument('asn_map_file')
    parser.add_argument('output_dir')
    args = parser.parse_args()

    FORMAT = '%(asctime)s %(levelname)s %(message)s'
    logging.basicConfig(
        format=FORMAT,
        level=logging.DEBUG,
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    ixp_file = args.ixp_file
    ixp_peers_file = args.ixp_peers_file
    interfaces_file = args.interfaces_file
    hegemony_file = args.hegemony_file
    asn_map_file = args.asn_map_file

    if check_missing_files([ixp_file, ixp_peers_file, interfaces_file, hegemony_file, asn_map_file, DECIX_LG, IXBR_LG, LINX_LG]):
        sys.exit(1)

    output_dir = sanitize_dir(args.output_dir)
    output_file_prefix = \
        os.path.basename(hegemony_file)[:-len(HEGEMONY_FILE_SUFFIX)]
    output_file = f'{output_dir}{output_file_prefix}{OUTPUT_FILE_SUFFIX}'

    ixp = read_ixp_file(ixp_file)
    ixp_peers = read_ixp_peers_file(ixp_peers_file)
    interfaces = read_interfaces_file(interfaces_file)
    hegemony = read_hegemony_file(hegemony_file, 0.1, 10)
    asn_cc = read_asn_country_map(asn_map_file)
    decix_lg_asns = read_lg_member_asns(DECIX_LG)
    ixbr_lg_asns = read_lg_member_asns(IXBR_LG)
    linx_lg_asns = read_lg_member_asns(LINX_LG)

    logging.info(f'Writing to {output_file}')
    with open(output_file, 'w') as f:
        headers = ('ix_id', 'org_id', 'name', 'name_long', 'cc', 'peers',
                   'peers_national', 'peers_international', 'peers_unknown',
                   'peers_seen', 'interfaces_seen', 'tr_count', 'dependencies',
                   'dependencies_national', 'dependencies_international',
                   'dependencies_unknown', 'dependent_peers',
                   'dependent_peers_national', 'dependent_peers_international',
                   'dependent_peers_unknown', 'peers_seen_r',
                   'dependencies_peers_r', 'peers_national_r',
                   'dependent_peers_r', 'dependent_peers_national_r')
        f.write(DATA_DELIMITER.join(headers) + '\n')
        for ix_id, ixp_info in ixp.items():
            peers = count_national_peers(ixp_peers[ix_id])
            deps = map_national(ixp_info.cc, hegemony[ix_id], asn_cc)
            dependent_peers = set(ixp_peers[ix_id].keys()).intersection(hegemony[ix_id])
            dep_peers = map_national(ixp_info.cc, dependent_peers, asn_cc)

            ixp_peers_count = sum(peers)
            if ixp_peers_count != ixp_info.peers:
                logging.warning(f'Number of peers in IXP info '
                                f'({ixp_info.peers}) does not match IXP-peers '
                                f'file ({ixp_peers_count}).')
            if ix_id == '31':
                logging.info(f'LG: {len(decix_lg_asns)} PDB: {len(ixp_peers[ix_id])}')
                num_peers = len(decix_lg_asns.union(ixp_peers[ix_id].keys()))
                if num_peers > ixp_info.peers:
                    logging.info(f'Added {num_peers - ixp_info.peers} new peers via looking glass for DE-CIX '
                                 f'Frankfurt. Total {num_peers}')
            elif ix_id == '171':
                logging.info(f'LG: {len(ixbr_lg_asns)} PDB: {len(ixp_peers[ix_id])}')
                num_peers = len(ixbr_lg_asns.union(ixp_peers[ix_id].keys()))
                if num_peers > ixp_info.peers:
                    logging.info(f'Added {num_peers - ixp_info.peers} new peers via looking glass for IX.br Sao '
                                 f'Paulo. Total {num_peers}')
            elif ix_id == '18':
                logging.info(f'LG: {len(linx_lg_asns)} PDB: {len(ixp_peers[ix_id])}')
                num_peers = len(linx_lg_asns.union(ixp_peers[ix_id].keys()))
                if num_peers > ixp_info.peers:
                    logging.info(f'Added {num_peers - ixp_info.peers} new peers via looking glass for LINX LON1. '
                                 f'Total {num_peers}')
            else:
                num_peers = ixp_info.peers
            peers_seen = len(interfaces[ix_id]['peer_asn'])
            dependencies = len(hegemony[ix_id])
            peers_national = deps[0]
            dependent_peers = sum(dep_peers)
            dep_peers_national = dep_peers[0]
            peers_seen_r = 0
            dependencies_peers_r = 0
            peers_national_r = 0
            dependent_peers_r = 0
            if num_peers > 0:
                peers_seen_r = peers_seen / num_peers
                dependencies_peers_r = dependencies / num_peers
                peers_national_r = peers_national / num_peers
                dependent_peers_r = dependent_peers / num_peers
            dependent_peers_national_r = 0
            if dependent_peers > 0:
                dependent_peers_national_r = dep_peers_national / dependent_peers

            line = (ixp_info.id,
                    ixp_info.org_id,
                    ixp_info.name,
                    ixp_info.name_long,
                    ixp_info.cc,
                    num_peers,
                    *peers,
                    peers_seen,
                    interfaces[ix_id]['interfaces'],
                    interfaces[ix_id]['tr_count'],
                    dependencies,
                    *deps,
                    dependent_peers,
                    *dep_peers,
                    peers_seen_r,
                    dependencies_peers_r,
                    peers_national_r,
                    dependent_peers_r,
                    dependent_peers_national_r)
            f.write(DATA_DELIMITER.join(map(str, line)) + '\n')


if __name__ == '__main__':
    main()
    sys.exit(0)
