import argparse
import bz2
import logging
import pickle
import sys
from collections import defaultdict

DATA_DELIMITER = ','


def read_ixp_file(ixp_file: str) -> dict:
    logging.info(f'Reading ix data from {ixp_file}')
    with bz2.open(ixp_file, 'r') as f:
        data = pickle.load(f)
    ix_list = data['ix']
    ix = {e['id']: e for e in ix_list}
    logging.info(f'Read {len(ix)} entries.')
    return ix


def read_netixlan_file(netixlan_file: str) -> list:
    logging.info(f'Reading netixlan data from {netixlan_file}')
    with bz2.open(netixlan_file, 'r') as f:
        data = pickle.load(f)
    logging.info(f'Read {len(data)} entries.')
    return data


def read_asn_country_map(asn_cc_map: str) -> dict:
    ret = dict()
    with open(asn_cc_map, 'r') as f:
        f.readline()
        for line in f:
            asn, count, cc = line.strip().split(DATA_DELIMITER)
            if int(count) > 1:
                cc = '**'
            ret[int(asn)] = cc
    return ret


def main() -> None:
    desc = """Convert data from raw PeeringDB dumps to CSV.
              The CSV contains one row per IXP, with information about the
              ix_id, org_id, name, country, and combined number of peers as
              well as split by IPv4/IPv6.
              Input data is expected in *.pickle.bz2 format as obtained by
              the internet-stats scripts
              (https://github.com/m-appel/internet-stats)"""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('ixp_file')
    parser.add_argument('netixlan_file')
    parser.add_argument('asn_map_file')
    parser.add_argument('output_file')
    args = parser.parse_args()

    FORMAT = '%(asctime)s %(levelname)s %(message)s'
    logging.basicConfig(
        format=FORMAT,
        level=logging.DEBUG,
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    ixp_file = args.ixp_file
    netixlan_file = args.netixlan_file
    asn_map_file = args.asn_map_file
    output_file = args.output_file

    ix = read_ixp_file(ixp_file)
    netixlan = read_netixlan_file(netixlan_file)
    asn_cc = read_asn_country_map(asn_map_file)

    # Map ix_id -> IPv4 peers.
    # Peers are represented by AS sets.
    ix_peers = defaultdict(set)
    for entry in netixlan:
        ix_id = entry['ix_id']
        asn = entry['asn']
        if entry['ipaddr4']:
            ix_peers[ix_id].add(asn)

    failed_cc_mappings = 0
    logging.info(f'Writing to output file {output_file}')
    with open(output_file, 'w') as f:
        headers = ('ix_id', 'org_id', 'peer_asn',
                   'ix_cc', 'peer_cc', 'national')
        f.write(DATA_DELIMITER.join(headers) + '\n')
        for ix_id, peer_asns in ix_peers.items():
            org_id = ix[ix_id]['org_id']
            ix_cc = ix[ix_id]['country']
            for asn in sorted(peer_asns):
                if asn in asn_cc:
                    peer_cc = asn_cc[asn]
                else:
                    logging.warning(f'Failed to find country mapping for ASN '
                                    f'{asn}')
                    failed_cc_mappings += 1
                    peer_cc = None
                if peer_cc is None:
                    national = None
                elif peer_cc == ix_cc:
                    national = True
                else:
                    national = False
                line = (ix_id, org_id, asn, ix_cc, peer_cc, national)
                f.write(DATA_DELIMITER.join(map(str, line)) + '\n')
    logging.info(f'Country mapping of {failed_cc_mappings} ASNs failed.')


if __name__ == '__main__':
    main()
    sys.exit(0)
