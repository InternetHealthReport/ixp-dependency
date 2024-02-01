import argparse
import bz2
import logging
import pickle
import sys
from collections import defaultdict, namedtuple
from datetime import datetime
from math import log2
from typing import Tuple
from socket import AF_INET

import radix
from numpy import round

Prefix = namedtuple('Prefix', 'prefix type rir cc status id')

DSF_DELIMITER = '|'
DSF_VERSION_LINE_FIELD_COUNT = 7
DSF_SUMMARY_LINE_FIELD_COUNT = 6
DSF_RECORD_LINE_MIN_FIELD_COUNT = 8
DSF_DATE_FMT = '%Y%m%d%z'
PP_DATE_FMT = '%Y-%m-%d%z'


def load_rib(rib_file: str) -> radix.Radix:
    with bz2.open(rib_file, 'rb') as f:
        return pickle.load(f)


def parse_version_line(line: str) -> None:
    line_strip = line.strip()
    line_split = line_strip.split(DSF_DELIMITER)
    field_count = len(line_split)
    if field_count != DSF_VERSION_LINE_FIELD_COUNT:
        logging.error(f'Version line has invalid number of fields. Expected: {DSF_VERSION_LINE_FIELD_COUNT} Got: '
                      f'{field_count}')
        logging.error(line_strip)
        return
    version = line_split[0]
    registry = line_split[1]
    serial = line_split[2]
    records = line_split[3]
    utcoffset = line_split[6]
    try:
        startdate = datetime.strptime(f'{line_split[4]}{utcoffset}', DSF_DATE_FMT)
        enddate = datetime.strptime(f'{line_split[5]}{utcoffset}', DSF_DATE_FMT)

    except ValueError as e:
        logging.error(f'Version line contains invalid date: {e}')
        logging.error(line_strip)
        return

    logging.info(f'   Version: {version}')
    logging.info(f'  Registry: {registry}')
    logging.info(f'    Serial: {serial}')
    logging.info(f'   Records: {records}')
    logging.info(f'Start date: {startdate.strftime(PP_DATE_FMT)}')
    logging.info(f'  End date: {enddate.strftime(PP_DATE_FMT)}')


def parse_summary_line(summary_line: str) -> int:
    line_strip = summary_line.strip()
    line_split = line_strip.split(DSF_DELIMITER)
    field_count = len(line_split)
    if field_count != DSF_SUMMARY_LINE_FIELD_COUNT:
        logging.error(f'Summary line has invalid number of fields. Expected: {DSF_SUMMARY_LINE_FIELD_COUNT} Got: '
                      f'{field_count}')
        logging.error(line_strip)
        return -1
    if line_split[1] != '*' or line_split[3] != '*' or line_split[5] != 'summary':
        logging.error(f'Malformed summary line. "*" or "summary" fields missing.')
        logging.error(line_strip)
        return -1
    summary_type = line_split[2]
    count = int(line_split[4])
    logging.info(f'{summary_type}: {count}')
    return count


def parse_record_line(record_line: str) -> Prefix:
    line_strip = record_line.strip()
    line_split = line_strip.split(DSF_DELIMITER)
    field_count = len(line_split)
    if field_count < DSF_RECORD_LINE_MIN_FIELD_COUNT:
        logging.error(f'Version line has too few fields. Expected at least: {DSF_RECORD_LINE_MIN_FIELD_COUNT} Got: '
                      f'{field_count}')
        logging.error(line_strip)
        return None
    registry = line_split[0]
    cc = line_split[1]
    type = line_split[2]
    start = line_split[3]
    value = int(line_split[4])
    status = line_split[6]
    id = line_split[7]
    if type == 'ipv4':
        netmask = 32 - log2(value)
        if netmask % 1:
            logging.debug(f'Non-CIDR netmask: {start}/{netmask}')
        netmask = int(round(netmask))
    elif type == 'ipv6':
        netmask = value
    else:
        return None
    return Prefix(f'{start}/{netmask}', type, registry, cc, status, id)


def load_prefix_map(delegated_stats: str) -> Tuple[radix.Radix, radix.Radix]:
    ipv4 = radix.Radix()
    ipv6 = radix.Radix()
    ipv4_records = 0
    ipv6_records = 0
    logging.info(f'Delegated stats: {delegated_stats}')
    with bz2.open(delegated_stats, 'rt') as f:
        parse_version_line(f.readline())
        asn_count = parse_summary_line(f.readline())
        ipv4_count = parse_summary_line(f.readline())
        ipv6_count = parse_summary_line(f.readline())
        if any([c < 0 for c in (asn_count, ipv4_count, ipv6_count)]):
            return dict(), dict()
        for line in f:
            prefix = parse_record_line(line)
            if prefix is None:
                continue
            if prefix.type == 'ipv4':
                n = ipv4.add(prefix.prefix)
                n.data['info'] = prefix
                ipv4_records += 1
            elif prefix.type == 'ipv6':
                n = ipv6.add(prefix.prefix)
                n.data['info'] = prefix
                ipv6_records += 1
    if ipv4_records != ipv4_count:
        logging.error(f'Number of IPv4 records does not match.')
        logging.error(f'Summary: {ipv4_count}')
        logging.error(f'Records: {ipv4_records}')
    if ipv6_records != ipv6_count:
        logging.error(f'Number of IPv6 records does not match.')
        logging.error(f'Summary: {ipv6_count}')
        logging.error(f'Records: {ipv6_records}')
    return ipv4, ipv6


def get_prefix_match(prefix: str, prefix_map: radix.Radix, include_covered: bool = False) -> list:
    n = prefix_map.search_best(prefix)
    if n:
        return [n.data['info']]
    if not include_covered:
        return list()
    covered = prefix_map.search_covered(prefix)
    if not covered:
        logging.debug(f'{prefix} is BOGON')
        return list()
    prefixes = list()
    for node in covered:
        node_prefix = node.data['info']
        prefixes.append(node_prefix)
    return prefixes

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('delegated_stats')
    parser.add_argument('rib_file')
    parser.add_argument('output_file')
    parser.add_argument('output_file_cc')
    parser.add_argument('--include-covered', action='store_true')
    args = parser.parse_args()

    FORMAT = '%(asctime)s %(levelname)s %(message)s'
    logging.basicConfig(
        format=FORMAT,
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    logging.info(f'Started: {sys.argv}')
    include_covered = args.include_covered
    if include_covered:
        logging.info(f'Including covered prefixes in set')

    rib_file = args.rib_file
    rtree = load_rib(rib_file)

    delegated_stats = args.delegated_stats
    ipv4, ipv6 = load_prefix_map(delegated_stats)
    if not ipv4:
        sys.exit(1)

    asn_prefixes = defaultdict(lambda: {'cc': set(), 'prefixes': list()})
    unallocated_prefixes = list()
    for node in rtree.nodes():
        asn = node.data['as'].strip('{}')
        if ',' in asn:
            # AS set -> ignore...
            continue
        prefix = node.prefix
        if node.family == AF_INET:
            prefix_info = get_prefix_match(prefix, ipv4, include_covered)
        else:
            prefix_info = get_prefix_match(prefix, ipv6, include_covered)
        if not prefix_info:
            continue

        used_prefixes = list()
        ccs = set()
        for prefix in prefix_info:
            if prefix.status != 'allocated' and prefix.status != 'assigned':
                # Bogon prefix
                unallocated_prefixes.append((asn, prefix))
                continue
            if prefix.cc == 'ZZ':
                # No country info
                logging.warning(f'Assigned prefix with ZZ country code: {asn} {prefix}')
                continue
            used_prefixes.append(prefix)
            ccs.add(prefix.cc)
        if not ccs:
            continue

        asn_prefixes[asn]['cc'].update(ccs)
        asn_prefixes[asn]['prefixes'] += used_prefixes

    output_file = args.output_file
    output_file_cc = args.output_file_cc
    asn_cc = list()
    pickleable = dict()
    for asn, prefixes in sorted(asn_prefixes.items(), key=lambda t: int(t[0])):
        pickleable[asn] = prefixes
        pickleable[asn]['cc'] = tuple(pickleable[asn]['cc'])
        asn_cc.append((asn, tuple(prefixes['cc'])))
    with bz2.open(output_file, 'wb') as f:
        pickle.dump(pickleable, f)
    with open(output_file_cc, 'w') as f:
        headers = ('asn', 'count', 'cc')
        f.write(','.join(headers) + '\n')
        for asn, cc in asn_cc:
            line = (asn, str(len(cc)), ';'.join(sorted(cc)))
            f.write(','.join(line) + '\n')


if __name__ == '__main__':
    main()
    sys.exit(0)
