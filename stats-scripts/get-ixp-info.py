
import argparse
import bz2
import logging
import pickle
import sys
from collections import defaultdict, namedtuple

DATA_DELIMITER = ','
Peers = namedtuple('Peers', 'v4 v6')


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
    output_file = args.output_file

    ix = read_ixp_file(ixp_file)
    netixlan = read_netixlan_file(netixlan_file)

    # Map ix_id -> (IPv4 peers, IPv6 peers).
    # Peers are represented by AS sets.
    ix_peers = defaultdict(lambda: Peers(set(), set()))
    for entry in netixlan:
        ix_id = entry['ix_id']
        asn = entry['asn']
        if entry['ipaddr4']:
            ix_peers[ix_id].v4.add(asn)
        if entry['ipaddr6']:
            ix_peers[ix_id].v6.add(asn)

    logging.info(f'Writing {len(ix)} lines to {output_file}.')
    with open(output_file, 'w') as f:
        headers = ('id', 'org_id', 'name', 'name_long', 'country',
                   'peers_combined', 'peers_v4', 'peers_v6')
        f.write(DATA_DELIMITER.join(headers) + '\n')
        for ix_id, ix_value in sorted(ix.items()):
            name = ix_value['name'].replace(',', ' ')
            name_long = ix_value['name_long'].replace(',', ' ')
            line = [ix_id, ix_value['org_id'], name, name_long, ix_value['country']]
            if ix_id not in ix_peers:
                # No peers found for this IXP.
                line += ['0'] * 3
            else:
                peers = ix_peers[ix_id]
                line.append(len(peers.v4.union(peers.v6)))
                line.append(len(peers.v4))
                line.append(len(peers.v6))
            f.write(DATA_DELIMITER.join(map(str, line)) + '\n')


if __name__ == '__main__':
    main()
    sys.exit(0)
