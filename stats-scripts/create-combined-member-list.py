import argparse
import bz2
import logging
import pickle
import sys

DATA_DELIMITER = ','


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


def read_peeringdb_members(netixlan_dump: str, ix_id: int) -> set:
    ret = set()
    with bz2.open(netixlan_dump, 'rb') as f:
        netixlan_data = pickle.load(f)
    for entry in netixlan_data:
        if entry['ix_id'] != ix_id or not entry['asn'] or not entry['ipaddr4']:
            continue
        ret.add(entry['asn'])
    return ret


def read_lg_asns(lg_member_asns: str) -> set:
    with open(lg_member_asns, 'r') as f:
        return {int(l.strip()) for l in f}


def main() -> None:
    desc = """Combine member information from PeeringDB and looking glass and also use conservative
           country mapping"""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('netixlan_dump')
    parser.add_argument('lg_member_asns')
    parser.add_argument('asn_map_file')
    parser.add_argument('ix_id', type=int)
    parser.add_argument('output_file')
    args = parser.parse_args()

    FORMAT = '%(asctime)s %(levelname)s %(message)s'
    logging.basicConfig(
        format=FORMAT,
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    ix_id = args.ix_id
    asn_country = read_asn_country_map(args.asn_map_file)
    pdb_members = read_peeringdb_members(args.netixlan_dump, ix_id)
    logging.info(f'Read {len(pdb_members)} PeeringDB members.')
    lg_members = read_lg_asns(args.lg_member_asns)
    logging.info(f'Read {len(lg_members)} looking glass members.')
    combined = pdb_members.union(lg_members)
    logging.info(f'Total: {len(combined)} members.')
    member_cc = list()
    failed_mappings = 0
    for asn in sorted(combined):
        if asn not in asn_country:
            failed_mappings += 1
            cc = 'ZZ'
        else:
            cc = asn_country[asn]
        member_cc.append((asn, cc))
    logging.info(f'Failed to map {failed_mappings} members.')

    with open(args.output_file, 'w') as f:
        header = ('member_asn', 'cc')
        f.write(DATA_DELIMITER.join(header) + '\n')
        for entry in member_cc:
            f.write(DATA_DELIMITER.join(map(str, entry)) + '\n')


if __name__ == '__main__':
    main()
    sys.exit(0)
