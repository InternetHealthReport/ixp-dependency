import argparse
import logging
import os
import sys
from collections import defaultdict, namedtuple

sys.path.append('../')
from tools.shared_functions import sanitize_dir

INPUT_FILE_SUFFIX = '.hegemony.csv'
OUTPUT_FILE_SUFFIX = '.ixp_regionality.csv'
DATA_DELIMITER = ','
IxpInfo = namedtuple('IxpInfo', 'name name_long cc peers')


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


def read_ixp_info(ixp_info_file: str) -> dict:
    ret = dict()
    with open(ixp_info_file, 'r') as f:
        f.readline()
        for line in f:
            line_split = line.strip().split(DATA_DELIMITER)
            ix_id = line_split[0]
            name = line_split[2].replace(',', ' ')
            name_long = line_split[3].replace(',', ' ')
            cc = line_split[4]
            peers = int(line_split[6])  # IPv4 peers
            ret[ix_id] = IxpInfo(name, name_long, cc, peers)
    return ret


def read_hegemony_file(input_file: str,
                       asn_country: dict,
                       ixp_info: dict,
                       min_hegemony_threshold: float = 0,
                       min_peer_threshold: int = 0) -> dict:
    ret = defaultdict(lambda: {'same': 0, 'other': 0})
    with open(input_file, 'r') as f:
        f.readline()
        for line in f:
            line_split = line.strip().split(DATA_DELIMITER)
            scope = line_split[0]
            asn = line_split[1]
            hegemony = float(line_split[2])
            peers = int(line_split[3])
            if not asn.startswith('ix|') \
                    or hegemony < min_hegemony_threshold \
                    or peers < min_peer_threshold \
                    or not scope.startswith('as|') \
                    or ';' in asn \
                    or hegemony > 1:
                continue
            ix_id = asn.removeprefix('ix|')
            if ix_id not in ixp_info:
                logging.warning(f'Failed to find info for IXP {ix_id}')
                continue
            scope = scope.removeprefix('as|')
            if scope not in asn_country:
                logging.warning(
                    f'Failed to find country mapping for AS {scope}')
                continue
            if ixp_info[ix_id].cc == asn_country[scope]:
                ret[ix_id]['same'] += 1
            else:
                ret[ix_id]['other'] += 1
    return ret


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file')
    parser.add_argument('asn_map_file')
    parser.add_argument('ixp_info_file')
    parser.add_argument('output_dir')
    args = parser.parse_args()

    FORMAT = '%(asctime)s %(levelname)s %(message)s'
    logging.basicConfig(
        format=FORMAT,
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    asn_file = args.asn_map_file
    logging.info(f'Reading AS -> country map from file: {asn_file}')
    asn_country = read_asn_country_map(asn_file)

    ixp_file = args.ixp_info_file
    logging.info(f'Reading IXP info from file: {ixp_file}')
    ixp_info = read_ixp_info(ixp_file)

    input_file = args.input_file
    if not input_file.endswith(INPUT_FILE_SUFFIX):
        logging.error(f'Expected input file with "{INPUT_FILE_SUFFIX}" file '
                      f'ending.')
        sys.exit(1)

    ixp_scope_region = read_hegemony_file(input_file,
                                          asn_country,
                                          ixp_info,
                                          0.1,
                                          10)

    output_dir = sanitize_dir(args.output_dir)
    output_file = f'{output_dir}' \
        f'{os.path.basename(input_file)[:-len(INPUT_FILE_SUFFIX)]}' \
        f'{OUTPUT_FILE_SUFFIX}'

    os.makedirs(output_dir, exist_ok=True)
    with open(output_file, 'w') as f:
        headers = ('ix_id', 'scopes', 'regionality', 'cc', 'name', 'name_long')
        f.write(f'{DATA_DELIMITER.join(headers)}\n')
        for ix_id in sorted(ixp_scope_region.keys(), key=lambda k: int(k)):
            scope_region = ixp_scope_region[ix_id]
            same = scope_region['same']
            other = scope_region['other']
            total = same + other
            regionality = same / total
            curr_ixp_info = ixp_info[ix_id]
            if curr_ixp_info.peers < 2:
                continue
            line = (ix_id, total, regionality, curr_ixp_info.cc,
                    curr_ixp_info.name, curr_ixp_info.name_long)
            f.write(f'{DATA_DELIMITER.join(map(str, line))}\n')


if __name__ == '__main__':
    main()
    sys.exit(0)
