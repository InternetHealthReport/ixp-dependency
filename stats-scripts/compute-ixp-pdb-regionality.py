import argparse
import logging
import sys
from collections import defaultdict

DATA_DELIMITER = ','
DECIX_LG = '../raw-data/lg-dumps/de-cix-fra-member-asns.csv'
IXBR_LG = '../raw-data/lg-dumps/ix-br-sp-member-asns.csv'
LINX_LG = '../raw-data/lg-dumps/linx-lon1-member-asns.csv'


def read_ixp_peers_file(input_file: str):
    ret = defaultdict(lambda: {'same': 0, 'other': 0})
    with open(input_file, 'r') as f:
        f.readline()
        for line in f:
            line_split = line.strip().split(DATA_DELIMITER)
            ix_id = line_split[0]
            ix_cc = line_split[3]
            peer_cc = line_split[4]
            if ix_cc != peer_cc:
                ret[ix_id]['other'] += 1
            else:
                ret[ix_id]['same'] += 1
    return ret


def get_ixp_peers(input_file: str):
    ix_cc_map = dict()
    ret = defaultdict(set)
    with open(input_file, 'r') as f:
        f.readline()
        for line in f:
            line_split = line.strip().split(DATA_DELIMITER)
            ix_id = line_split[0]
            peer_asn = line_split[2]
            ix_cc = line_split[3]
            ix_cc_map[ix_id] = ix_cc
            ret[ix_id].add(peer_asn)
    return ix_cc_map, ret


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('ixp_peers_file')
    parser.add_argument('asn_map_file')
    parser.add_argument('output_file')
    args = parser.parse_args()

    FORMAT = '%(asctime)s %(levelname)s %(message)s'
    logging.basicConfig(
        format=FORMAT,
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    ixp_peers_file = args.ixp_peers_file
    asn_map_file = args.asn_map_file

    ixp_peer_data = read_ixp_peers_file(ixp_peers_file)
    ixp_ccs, ixp_peer_asns = get_ixp_peers(ixp_peers_file)
    lg_asns = {'18': read_lg_member_asns(LINX_LG),
               '31': read_lg_member_asns(DECIX_LG),
               '171': read_lg_member_asns(IXBR_LG)}
    asn_cc = read_asn_country_map(asn_map_file)

    output_file = args.output_file

    with open(output_file, 'w') as f:
        headers = ('ix_id', 'peers', 'regionality')
        f.write(f'{DATA_DELIMITER.join(headers)}\n')
        for ix_id in sorted(ixp_peer_data.keys(), key=lambda k: int(k)):
            peer_region = ixp_peer_data[ix_id]
            same = peer_region['same']
            other = peer_region['other']
            if ix_id in lg_asns:
                logging.info(f'Checking LG ASNs for ix_id {ix_id}')
                new_asns = lg_asns[ix_id] - ixp_peer_asns[ix_id]
                logging.info(f'Found {len(new_asns)} new ASNs.')
                logging.info(f'pre: same:{same} other:{other}')
                for asn in new_asns:
                    if asn not in asn_cc:
                        logging.warning(f'Failed to find country mapping for AS{asn}')
                        continue
                    if asn_cc[asn] != ixp_ccs[ix_id]:
                        other += 1
                    else:
                        same += 1
                logging.info(f'post: same:{same} other:{other} total:{same + other}')
            total = same + other
            if total < 2:
                continue
            regionality = same / total
            line = (ix_id, total, regionality)
            f.write(f'{DATA_DELIMITER.join(map(str, line))}\n')


if __name__ == '__main__':
    main()
    sys.exit(0)
