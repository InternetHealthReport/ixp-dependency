from tools.shared_functions import sanitize_dir
import argparse
import bz2
import logging
import os
import pickle
import sys
from collections import defaultdict
from typing import Tuple

import numpy as np
from numpy import isclose

sys.path.append('../')

INPUT_FILE_SUFFIX = '.hegemony.csv'
OUTPUT_FILE_SUFFIX = '.per_as_ixp_dependencies.csv'
DETAIL_OUTPUT_FILE_SUFFIX = '.per_scope_details.pickle.bz2'
DATA_DELIMITER = ','

AS0 = '0'

# We need to take into account all entries belonging to an IXP for a
# single scope, before we can decide where to assign it.
# If there are n ix_asn entries, whose scores add up to
# the total of ix, we have a "shared" dependency over n participants.
#
# If there is an ix_0 entry with score equal to ix or ix_0 an ix_asn
# add up to ix, we have a shared dependency over n participants (if
# any) and some number of interfaces.
#   1. If there are m ips whose score adds up to ix_0, we have m
#      interfaces.
#   2. If there are no ips or the scores do not add up, we have to
#      count _all_ interfaces for asn 0 over which the scope was
#      reached
#
# If there are only ix_asn entries, but they don't add up to ix, we
# need to check if the scope was reached over asn 0 interfaces.
#   1. If not, we have a shared dependency over all participants
#      over which the scope was reached
#   2. If yes, we have a shared dependency over all participants and
#      all asn 0 interfaces
# The same process holds if there is only an ix entry.
#
# If there are only asn 0 interfaces, we have a really unknown
# dependency over m interfaces.


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


def read_per_scope_interfaces(input_file: str) -> dict:
    # ix
    #   -> scope
    #     -> by-ix
    #       -> ix-id: asn -> set of ips
    #     -> by-ip: ip -> (ix_id, asn)
    ret = defaultdict(lambda: {'by-ix': defaultdict(lambda: defaultdict(set)), 'by-ip': dict()})
    with bz2.open(input_file, 'rt') as f:
        f.readline()
        for line in f:
            line_split = line.strip().split(DATA_DELIMITER)
            ix_id = line_split[0]
            asn = line_split[1]
            ip = line_split[2]
            scope = line_split[3]
            ret[scope]['by-ix'][ix_id][asn].add(ip)
            ret[scope]['by-ip'][ip] = (ix_id, asn)
    return ret


def read_hegemony_file(input_file: str,
                       per_scope_interfaces: dict,
                       min_hegemony_threshold: float = 0,
                       min_peer_threshold: int = 0) -> dict:
    ret = defaultdict(lambda: defaultdict(lambda: {'general': None,
                                                   'per-as': defaultdict(lambda: {'direct': None,
                                                                                  'via-ip': list()})}))
    with open(input_file, 'r') as f:
        f.readline()
        for line in f:
            line_split = line.strip().split(DATA_DELIMITER)
            scope = line_split[0]
            asn = line_split[1]
            hegemony = float(line_split[2])
            peers = int(line_split[3])
            if ((not asn.startswith('ix|') and not asn.startswith('ip|'))
                    or not scope.startswith('as|')):
                continue
            scope = scope.removeprefix('as|')
            if asn.startswith('ip|'):
                # IP
                ip = asn.removeprefix('ip|')
                if ip not in per_scope_interfaces[scope]['by-ip']:
                    logging.error('Scope was never reached via ip, but has dependency')
                    logging.error(f'scope:{scope} ip:{ip}')
                    logging.error(per_scope_interfaces[scope])
                    sys.exit(1)
                ix_id, ix_asn = per_scope_interfaces[scope]['by-ip'][ip]
                ret[ix_id][scope]['per-as'][ix_asn]['via-ip'].append((ip, hegemony, peers))
                continue
            elif ';' in asn:
                # per_as
                ix_id, ix_asn = asn.removeprefix('ix|').split(';')
                ix_asn = ix_asn.removeprefix('as|')
                value = (hegemony, peers)
                if ret[ix_id][scope]['per-as'][ix_asn]['direct'] is not None:
                    logging.error('Duplicate per-AS dependency. Should never happen!')
                    logging.error(f'ix_id:{ix_id} scope:{scope} asn:{ix_asn} '
                                  f'existing:{ret[ix_id][scope]["per-as"][ix_asn]["direct"]} new:{value}')
                ret[ix_id][scope]['per-as'][ix_asn]['direct'] = value
                continue
            # General
            if hegemony < min_hegemony_threshold or peers < min_peer_threshold or hegemony > 1:
                # We can filter here, because if the general
                # dependency is already filtered, we do not need to
                # process the scope for this IXP later.
                # Per-AS dependencies should be smaller or equal.
                continue
            ix_id = asn.removeprefix('ix|')
            value = (hegemony, peers)
            if ret[ix_id][scope]['general'] is not None:
                logging.error('Duplicate general IXP dependency. Should never happen!')
                logging.error(f'ix_id:{ix_id} scope:{scope} existing:{ret[ix_id][scope]["general"]} '
                              f'new:{value}')
            ret[ix_id][scope]['general'] = value
    return ret


def get_ix_asns(scope: str, ix_id: str, per_scope_interfaces: dict) -> dict:
    if scope not in per_scope_interfaces or ix_id not in per_scope_interfaces[scope]['by-ix']:
        logging.critical('Scope not in per_scope_interfaces or no entry for ix_id.')
        logging.critical('scope:{scope} ix_id:{ix_id}')
        sys.exit(1)
    ix_asns = per_scope_interfaces[scope]['by-ix'][ix_id]
    if not ix_asns:
        logging.critical('No ASes in per_scope_interfaces for scope/ix_id.')
        logging.critical(f'scope:{scope} ix_id:{ix_id}')
        sys.exit(1)
    return ix_asns


def only_as_0(scope: str, ix_id: str, per_scope_interfaces: dict) -> bool:
    ix_asns = get_ix_asns(scope, ix_id, per_scope_interfaces).keys()
    if len(ix_asns) > 1:
        return False
    if AS0 in ix_asns:
        return True
    return False


def only_known_as(scope: str, ix_id: str, per_scope_interfaces: dict) -> bool:
    ix_asns = get_ix_asns(scope, ix_id, per_scope_interfaces).keys()
    return AS0 not in ix_asns


def get_as_0_interfaces(scope: str, ix_id: str, per_scope_interfaces: dict) -> set:
    ix_asns = get_ix_asns(scope, ix_id, per_scope_interfaces)
    if AS0 not in ix_asns:
        logging.critical('No AS0 interfaces for scope/ix_id (unexpected).')
        logging.critical(f'scope:{scope} ix_id:{ix_id}')
        sys.exit(1)
    return ix_asns[AS0]


def get_known_ases(scope: str, ix_id: str, per_scope_interfaces: dict) -> set:
    ix_asns = set(get_ix_asns(scope, ix_id, per_scope_interfaces).keys())
    if AS0 in ix_asns:
        logging.critical('get_known_ases should only be called if there are only known ASes in ix_ases. Use get_all '
                         'to get a combination of known ASes and AS0 interfaces.')
        sys.exit(1)
    return ix_asns


def get_all(scope: str, ix_id: str, per_scope_interfaces: dict, expect_as_0: bool = False) -> Tuple[set, set]:
    ix_asns = get_ix_asns(scope, ix_id, per_scope_interfaces)
    if expect_as_0 and AS0 not in ix_asns:
        logging.critical('No AS0 interfaces for scope/ix_id (unexpected).')
        logging.critical(f'scope:{scope} ix_id:{ix_id}')
        sys.exit(1)
    ix_asn_set = set(ix_asns.keys())
    as_0_interfaces = set()
    if AS0 in ix_asn_set:
        as_0_interfaces = ix_asns[AS0]
        ix_asn_set.remove(AS0)
    return ix_asn_set, as_0_interfaces


def get_interfaces_and_hegemony_scores(ix_asn: str, per_as_deps: dict) -> Tuple[set, list]:
    interfaces = set()
    hegemony_scores = list()
    for ip, hege, peers in per_as_deps[ix_asn]['via-ip']:
        interfaces.add(ip)
        hegemony_scores.append(hege)
    return interfaces, hegemony_scores


def get_per_asn_asns_and_heges(per_as_deps: dict) -> Tuple[set, list]:
    ix_asns = set()
    hegemony_scores = list()
    for ix_asn in per_as_deps:
        ix_asns.add(ix_asn)
        hege_peers = per_as_deps[ix_asn]['direct']
        if hege_peers is None:
            logging.critical('Direct AS hegemony value is None')
            logging.critical(f'ix_asn:{ix_asn}')
            sys.exit(1)
        hegemony_scores.append(hege_peers[0])
    return ix_asns, hegemony_scores


def map_dependencies(ixp_dependencies: dict,
                     per_scope_interfaces: dict,
                     asn_country: dict):
    # ret[ix_id][cc][single/multiple/mixed/unknown]
    #   1. single: scope depends only on a single participant AS (count)
    #   2. multiple: scope depends on multiple participants, but we can identify all of
    #      them (count, set(AS))
    #   3. mixed: scope depends on at least one known participant and at least one
    #      unknown interface (count, set(AS), set(IP))
    #   4. unknown: scope depends only on unknown interfaces (count, set(IP))
    #
    # Details
    #  Single: map participant to list of scopes
    #  Multiple: use set of participant ASes as key to map to list of scopes
    ret = defaultdict(lambda: defaultdict(lambda: {'single': defaultdict(int),
                                                   'multiple': [0, set()],
                                                   'mixed': [0, set(), set()],
                                                   'unknown': [0, set()],
                                                   'general': 0}))
    details = defaultdict(lambda: defaultdict(lambda: {'single': defaultdict(list),
                                                       'multiple': defaultdict(list)}))
    ix_summary = defaultdict(lambda: {'general': [0, set(), set()], 'single': [0, set()], 'multiple': [0, set()],
                                      'mixed': [0, set(), set()], 'unknown': [0, set()]})
    for ix_id, scopes in ixp_dependencies.items():
        for scope in scopes.keys():
            if scopes[scope]['general'] is None:
                # Main IX dependency was already filtered.
                continue
            # Scope depends on IXP.
            if scope not in asn_country:
                logging.warning(f'No country mapping for scope: {scope}')
                cc = 'ZZ'
            else:
                cc = asn_country[scope]
            ret[ix_id][cc]['general'] += 1
            general_hege = scopes[scope]['general'][0]
            per_as_deps: dict = scopes[scope]['per-as']
            if not per_as_deps:
                # No per-AS dependency
                # Check per_scope_interfaces for other ASes.
                # Only AS 0?
                #   Scope can depend on all interfaces for AS 0 listed in
                #   per_scope_interfaces, ix_asn unknown. [4]
                # Only known ASes?
                #   Scope can depend on all ASes listed. Shared over known ASes. [2]
                # Both?
                #   Scope can depend on all ASes listed, as well as all interfaces for
                #   AS 0, shared over known and unknown ASes/interfaces [3]
                if only_as_0(scope, ix_id, per_scope_interfaces):
                    ret[ix_id][cc]['unknown'][0] += 1
                    ret[ix_id][cc]['unknown'][1].update(get_as_0_interfaces(scope,
                                                                            ix_id,
                                                                            per_scope_interfaces))
                elif only_known_as(scope, ix_id, per_scope_interfaces):
                    known_ases = get_known_ases(scope, ix_id, per_scope_interfaces)
                    ret[ix_id][cc]['multiple'][0] += 1
                    ret[ix_id][cc]['multiple'][1].update(known_ases)
                    key = tuple(sorted(known_ases))
                    details[ix_id][cc]['multiple'][key].append(scope)
                else:
                    ix_asns, as_0_interfaces = get_all(scope,
                                                       ix_id,
                                                       per_scope_interfaces,
                                                       expect_as_0=True)
                    ret[ix_id][cc]['mixed'][0] += 1
                    ret[ix_id][cc]['mixed'][1].update(ix_asns)
                    ret[ix_id][cc]['mixed'][2].update(as_0_interfaces)
            elif len(per_as_deps) == 1:
                # Single per-AS dependency.
                # If hege == general_hege:
                #   If AS != 0:
                #     Scope depends entirely on ix_asn (maybe multiple interfaces, but
                #     we don't care) [1]
                #   else: (AS == 0)
                #     Check if IP entry exists.
                #     If yes:
                #       More than one?
                #       If yes:
                #         If sum of IP hege == general_hege:
                #           Scope depends entirely on these interfaces, ix_asn unknown
                #           [4]
                #         else:
                #           Scope can depend on all interfaces for AS 0 listed in
                #           per_scope_interfaces, ix_asn unknown [4]
                #       else: (one IP only)
                #         If IP hege == general_hege:
                #           Scope depends entirely on interface, ix_asn unknown [4]
                #         else: (IP hege != general_hege)
                #           Scope can depend on all interfaces for AS 0 listed in
                #           per_scope_interfaces, ix_asn unknown [4]
                #     else: (no IP)
                #       Scope can depend on all interfaces for AS 0 listed in
                #       per_scope_interfaces, ix_asn unknown [4]
                # elif hege < general_hege:
                #   There are other dependencies, but maybe too small to list. Check
                #   per_scope_interfaces for other ASes.
                #   ASSERT: There must be other ASes.
                #   Only AS 0?
                #     ASSERT IMPOSSIBLE: If there are only AS 0 interfaces, there needs
                #     to be a AS 0 dependency with hege == general_hege.
                #   Only known ASes?
                #     Scope can depend on all ASes listed, shared over known ASes. [2]
                #   Both?
                #     Scope can depend on all ASes listed, as well as all interfaces for
                #     AS 0, shared over known and unknown ASes/interfaces [3]
                # else: (hege > general_hege)
                #   ASSERT IMPOSSIBLE / Ignore scope, because it's weird
                ix_asn = tuple(per_as_deps.keys())[0]
                hege_peers = per_as_deps[ix_asn]['direct']
                if hege_peers is None:
                    logging.critical('Direct AS hegemony value is None')
                    logging.critical(f'ix_id:{ix_id} scope:{scope} ix_asn:{ix_asn}')
                    sys.exit(1)
                hege = hege_peers[0]
                if hege == general_hege:
                    if ix_asn != AS0:
                        ret[ix_id][cc]['single'][ix_asn] += 1
                        details[ix_id][cc]['single'][ix_asn].append(scope)
                    else:
                        # ix_asn == AS0
                        interfaces, heges = get_interfaces_and_hegemony_scores(ix_asn, per_as_deps)
                        if not heges:
                            ret[ix_id][cc]['unknown'][0] += 1
                            ret[ix_id][cc]['unknown'][1].update(get_as_0_interfaces(scope,
                                                                                    ix_id,
                                                                                    per_scope_interfaces))
                        else:
                            # One or more AS0 interfaces.
                            hege_sum = sum(heges)
                            if isclose(hege_sum, general_hege):
                                ret[ix_id][cc]['unknown'][0] += 1
                                ret[ix_id][cc]['unknown'][1].update(interfaces)
                            elif hege_sum > general_hege:
                                logging.critical('Sum of AS0 interface dependencies larger than general.')
                                logging.critical(f'ix_id:{ix_id} scope:{scope} ix_asn:{ix_asn} general:{general_hege} '
                                                 f'interface_heges:{heges}')
                                sys.exit(1)
                            else:
                                ret[ix_id][cc]['unknown'][0] += 1
                                ret[ix_id][cc]['unknown'][1].update(get_as_0_interfaces(scope,
                                                                                        ix_id,
                                                                                        per_scope_interfaces))
                elif hege < general_hege:
                    ix_asns, as_0_interfaces = get_all(scope, ix_id, per_scope_interfaces)
                    if not ix_asns:
                        logging.critical('Only AS0 interfaces, but no AS0 dependency.')
                        logging.critical(f'ix_id:{ix_id} scope:{scope} ix_asn:{ix_asn}')
                        sys.exit(1)
                    if ix_asn != AS0 and ix_asn not in ix_asns:
                        logging.critical('Per-AS dependency not in per_scope_interfaces.')
                        logging.critical(f'ix_id:{ix_id} scope:{scope} ix_asn:{ix_asn}')
                        sys.exit(1)
                    if (not ix_asns - set(ix_asn)) and not as_0_interfaces:
                        logging.critical('There should be other ASes / AS0 interfaces.')
                        logging.critical(f'ix_id:{ix_id} scope:{scope} ix_asn:{ix_asn}')
                        sys.exit(1)
                    if not as_0_interfaces:
                        ret[ix_id][cc]['multiple'][0] += 1
                        ret[ix_id][cc]['multiple'][1].update(ix_asns)
                        key = tuple(sorted(ix_asns))
                        details[ix_id][cc]['multiple'][key].append(scope)
                    else:
                        ret[ix_id][cc]['mixed'][0] += 1
                        ret[ix_id][cc]['mixed'][1].update(ix_asns)
                        ret[ix_id][cc]['mixed'][2].update(as_0_interfaces)
                else:
                    logging.warning('Weird case were per-AS hegemony is larger than general.')
                    logging.warning(f'ix_id:{ix_id} scope:{scope} ix_asn:{ix_asn} general:{general_hege} '
                                    f'per-as:{hege}')
            else:
                # More than one per-AS dependency.
                # If sum of per-AS hege == general_hege:
                #   If no AS 0:
                #     Scope depends on the per-AS dependencies, shared over known ASes.
                #     [2]
                #   else: (AS 0 exists)
                #     Check if IP entry exists for AS 0.
                #     If yes:
                #       More than one?
                #       If yes:
                #         If sum of IP hege == AS 0 hege:
                #           Scope depends on per-AS dependencies and these interfaces,
                #           shared over known/unknown ASes/interfaces [3]
                #         else:
                #           Scope depends on per-AS dependencies and can depend on all
                #           interfaces for AS 0 listed in per_scope_interfaces, shared
                #           over known/unknown
                #           ASes/interfaces [3]
                #       else: (one IP only)
                #         If IP hege == AS 0 hege:
                #           Scope depends on per-AS dependencies and this interface,
                #           shared over known/unknown ASes/interfaces [3]
                #         else: (IP hege != AS 0 hege)
                #           Scope depends on per-AS dependencies and can depend on all
                #           interfaces for AS 0 listed in per_scope_interfaces, shared
                #           over known/unknown
                #           ASes/interfaces [3]
                #     else: (no IP entry for AS 0)
                #       Scope depends on per-AS dependencies and can depend on all
                #       interfaces for AS 0 listed in per_scope_interfaces, shared over
                #       known/unknown ASes/interfaces [3]
                # elif sum of per-AS hege < general_hege:
                #   There are other dependencies, but maybe too small to list. Check
                #   per_scope_interfaces for other ASes.
                #   ASSERT: There must be other ASes.
                #   Only AS 0?
                #     ASSERT IMPOSSIBLE
                #   Only known ASes?
                #     Scope can depend on all ASes listed, shared over known ASes. [2]
                #   Both?
                #     Scope can depend on all ASes listed, as well as all interfaces for
                #     AS 0, shared over known and unknown ASes/interfaces [3]
                # else: (sum of per-AS hege > general_hege)
                #   ASSERT IMPOSSIBLE / Ignore scope, because it's weird
                per_asn_asns, heges = get_per_asn_asns_and_heges(per_as_deps)
                hege_sum = sum(heges)
                if isclose(hege_sum, general_hege):
                    if AS0 not in per_asn_asns:
                        ret[ix_id][cc]['multiple'][0] += 1
                        ret[ix_id][cc]['multiple'][1].update(per_asn_asns)
                        key = tuple(sorted(per_asn_asns))
                        details[ix_id][cc]['multiple'][key].append(scope)
                    else:
                        # AS0 in per_asn_asns
                        as_0_interfaces_with_hege, as_0_heges = get_interfaces_and_hegemony_scores(AS0, per_as_deps)
                        if not as_0_interfaces_with_hege:
                            ret[ix_id][cc]['mixed'][0] += 1
                            ret[ix_id][cc]['mixed'][1].update(per_asn_asns)
                            ret[ix_id][cc]['mixed'][2].update(get_as_0_interfaces(scope, ix_id, per_scope_interfaces))
                        else:
                            # One or more AS0 interface with hegemony score.
                            as0_heges_sum = sum(as_0_heges)
                            if isclose(as0_heges_sum, general_hege):
                                ret[ix_id][cc]['mixed'][0] += 1
                                ret[ix_id][cc]['mixed'][1].update(per_asn_asns)
                                ret[ix_id][cc]['mixed'][2].update(as_0_interfaces_with_hege)
                            elif as0_heges_sum > general_hege:
                                logging.critical('Sum of AS0 interface dependencies larger than general.')
                                logging.critical(f'ix_id:{ix_id} scope:{scope} ix_asn:{per_asn_asns} '
                                                 f'general:{general_hege} interface_heges:{as_0_heges}')
                                sys.exit(1)
                            else:
                                ret[ix_id][cc]['mixed'][0] += 1
                                ret[ix_id][cc]['mixed'][1].update(per_asn_asns)
                                ret[ix_id][cc]['mixed'][2].update(get_as_0_interfaces(scope,
                                                                                      ix_id,
                                                                                      per_scope_interfaces))
                elif hege_sum < general_hege:
                    ix_asns, as_0_interfaces = get_all(scope, ix_id, per_scope_interfaces)
                    if not ix_asns:
                        logging.critical('Only AS0 interfaces, but no AS0 dependency.')
                        logging.critical(f'ix_id:{ix_id} scope:{scope} ix_asn:{per_asn_asns}')
                        sys.exit(1)
                    if (not ix_asns - per_asn_asns) and not as_0_interfaces:
                        logging.critical('There should be other ASes / AS0 interfaces.')
                        logging.critical(f'ix_id:{ix_id} scope:{scope} ix_asn:{per_asn_asns}')
                        # TODO REMOVE?
                        if not as_0_interfaces:
                            ret[ix_id][cc]['multiple'][0] += 1
                            ret[ix_id][cc]['multiple'][1].update(ix_asns)
                            key = tuple(sorted(ix_asns))
                            details[ix_id][cc]['multiple'][key].append(scope)
                        else:
                            ret[ix_id][cc]['mixed'][0] += 1
                            ret[ix_id][cc]['mixed'][1].update(ix_asns)
                            ret[ix_id][cc]['mixed'][2].update(as_0_interfaces)
                        continue
                    if not as_0_interfaces:
                        ret[ix_id][cc]['multiple'][0] += 1
                        ret[ix_id][cc]['multiple'][1].update(ix_asns)
                        key = tuple(sorted(ix_asns))
                        details[ix_id][cc]['multiple'][key].append(scope)
                    else:
                        ret[ix_id][cc]['mixed'][0] += 1
                        ret[ix_id][cc]['mixed'][1].update(ix_asns)
                        ret[ix_id][cc]['mixed'][2].update(as_0_interfaces)
                else:
                    logging.warning('Weird case were sum of per-AS hegemony is larger than general.')
                    logging.warning(f'ix_id:{ix_id} scope:{scope} general:{general_hege} sum:{hege_sum}')
    for ix_id, ccs in ret.items():
        for per_country_vals in ccs.values():
            ix_summary[ix_id]['general'][0] += per_country_vals['general']
            ix_summary[ix_id]['general'][1].update(per_country_vals['multiple'][1])
            ix_summary[ix_id]['general'][1].update(per_country_vals['mixed'][1])
            ix_summary[ix_id]['general'][2].update(per_country_vals['mixed'][2])
            ix_summary[ix_id]['general'][2].update(per_country_vals['unknown'][1])

            ix_summary[ix_id]['multiple'][0] += per_country_vals['multiple'][0]
            ix_summary[ix_id]['multiple'][1].update(per_country_vals['multiple'][1])

            ix_summary[ix_id]['mixed'][0] += per_country_vals['mixed'][0]
            ix_summary[ix_id]['mixed'][1].update(per_country_vals['mixed'][1])

            ix_summary[ix_id]['unknown'][0] += per_country_vals['unknown'][0]
            ix_summary[ix_id]['unknown'][1].update(per_country_vals['unknown'][1])

            for ix_asn, single_count in per_country_vals['single'].items():
                ix_summary[ix_id]['general'][1].add(ix_asn)
                ix_summary[ix_id]['single'][0] += single_count
                ix_summary[ix_id]['single'][1].add(ix_asn)

    return ret, ix_summary, details


def calculate_stats(hegemony: list) -> Tuple[float, float, float, float]:
    min = np.min(hegemony)
    mean = np.mean(hegemony)
    median = np.median(hegemony)
    max = np.max(hegemony)
    return min, mean, median, max


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file')
    parser.add_argument('per_scope_interfaces')
    parser.add_argument('asn_map_file')
    parser.add_argument('output_dir')
    args = parser.parse_args()

    FORMAT = '%(asctime)s %(levelname)s %(message)s'
    logging.basicConfig(
        format=FORMAT,
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    input_file = args.input_file
    if not input_file.endswith(INPUT_FILE_SUFFIX):
        logging.error(f'Expected input file with "{INPUT_FILE_SUFFIX}" file ending.')
        sys.exit(1)

    output_dir = sanitize_dir(args.output_dir)
    output_file = f'{output_dir}' \
                  f'{os.path.basename(input_file)[:-len(INPUT_FILE_SUFFIX)]}' \
                  f'{OUTPUT_FILE_SUFFIX}'
    detail_output_file = f'{output_dir}' \
        f'{os.path.basename(input_file)[:-len(INPUT_FILE_SUFFIX)]}' \
        f'{DETAIL_OUTPUT_FILE_SUFFIX}'

    asn_file = args.asn_map_file
    logging.info(f'Reading AS -> country map from file: {asn_file}')
    asn_country = read_asn_country_map(asn_file)

    per_scope_interfaces_file = args.per_scope_interfaces
    logging.info(f'Reading per-scope interfaces from file: {per_scope_interfaces_file}')
    per_scope_interfaces = read_per_scope_interfaces(per_scope_interfaces_file)

    hegemony_values = read_hegemony_file(input_file, per_scope_interfaces, 0.1, 10)
    ixp_dependencies, ixp_overview, ixp_details = map_dependencies(
        hegemony_values, per_scope_interfaces, asn_country)

    out = dict()
    for ix_id, ix_data in ixp_details.items():
        out[ix_id] = dict()
        for cc, per_cc_data in ix_data.items():
            out[ix_id][cc] = dict()
            for k, v in per_cc_data.items():
                out[ix_id][cc][k] = v
            if not out[ix_id][cc]:
                out[ix_id].pop(cc)
        if not out[ix_id]:
            out.pop(ix_id)
    with bz2.open(detail_output_file, 'wb') as f:
        pickle.dump(out, f)

    os.makedirs(output_dir, exist_ok=True)
    with open(output_file, 'w') as f:
        headers = ('ix_id', 'cc', 'asn', 'scopes', 'asn_count', 'interface_count')
        f.write(DATA_DELIMITER.join(headers) + '\n')
        for ix_id, ccs in sorted(ixp_dependencies.items(), key=lambda t: int(t[0])):
            overview = ixp_overview[ix_id]
            line = (ix_id, 'overview', 'general', overview['general'][0], len(overview['general'][1]),
                    len(overview['general'][2]))
            f.write(DATA_DELIMITER.join(map(str, line)) + '\n')
            line = (ix_id, 'overview', 'single',overview['single'][0], len(overview['single'][1]), 0)
            f.write(DATA_DELIMITER.join(map(str, line)) + '\n')
            line = (ix_id, 'overview', 'unknown', overview['unknown'][0], 0, len(overview['unknown'][1]))
            f.write(DATA_DELIMITER.join(map(str, line)) + '\n')
            line = (ix_id, 'overview', 'mixed', overview['mixed'][0], len(overview['mixed'][1]),
                    len(overview['mixed'][2]))
            f.write(DATA_DELIMITER.join(map(str, line)) + '\n')
            line = (ix_id, 'overview', 'multiple', overview['multiple'][0], len(overview['multiple'][1]), 0)
            f.write(DATA_DELIMITER.join(map(str, line)) + '\n')
            for cc in sorted(ccs):
                single = ccs[cc]['single']
                multiple = ccs[cc]['multiple']
                mixed = ccs[cc]['mixed']
                unknown = ccs[cc]['unknown']
                general = ccs[cc]['general']
                line = (ix_id, cc, 'general', general, 0, 0)
                f.write(DATA_DELIMITER.join(map(str, line)) + '\n')
                line = (ix_id, cc, 'unknown', unknown[0], 0, len(unknown[1]))
                f.write(DATA_DELIMITER.join(map(str, line)) + '\n')
                line = (ix_id, cc, 'mixed', mixed[0], len(mixed[1]), len(mixed[2]))
                f.write(DATA_DELIMITER.join(map(str, line)) + '\n')
                line = (ix_id, cc, 'multiple', multiple[0], len(multiple[1]), 0)
                f.write(DATA_DELIMITER.join(map(str, line)) + '\n')
                for asn in single:
                    line = (ix_id, cc, asn, single[asn], 1, 0)
                    f.write(DATA_DELIMITER.join(map(str, line)) + '\n')


if __name__ == '__main__':
    main()
    sys.exit(0)
