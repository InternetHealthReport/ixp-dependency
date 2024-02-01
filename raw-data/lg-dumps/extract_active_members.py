import argparse
import bz2
import pickle
import sys

# These were extracted manually.
# Keys for:
#   DE-CIX Frankfurt
#   IX.br São Paulo
#   LINX LON1
routeservers = {'de-cix': ['rs1_fra_ipv4', 'rs2_fra_ipv4', 'rsbh1_fra_ipv4'],
                'ix-br': ['SP-rs2-v4'],
                'linx': ['rs1-in2-lon1-linx-net-v4', 'rs3-tch-lon1-linx-net-v4']}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('raw_dump')
    parser.add_argument('output_file')
    args = parser.parse_args()

    raw_dump = args.raw_dump
    ix_name = raw_dump.split('.')[0]
    if ix_name not in routeservers:
        sys.exit('Unknown IXP.')
    with bz2.open(raw_dump, 'r') as f:
        neighbors = pickle.load(f)['neighbors']

    rs_neighbor_asns = set()
    for rs in routeservers[ix_name]:
        neighbor_key = 'neighbors'
        if neighbor_key not in neighbors[rs]:
            neighbor_key = 'neighbours'
        for neighbor in neighbors[rs][neighbor_key]:
            if neighbor['state'] != 'up':
                continue
            rs_neighbor_asns.add(neighbor['asn'])

    with open(args.output_file, 'w') as f:
        f.write('\n'.join(map(str, sorted(rs_neighbor_asns))) + '\n')


if __name__ == '__main__':
    main()
    sys.exit(0)
