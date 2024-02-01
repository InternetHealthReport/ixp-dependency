#!/bin/bash
set -euo pipefail

readonly STATS="../stats"
readonly NETIXLAN_DUMP="${STATS}/peeringdb/20221006-peeringdb-netixlan.pickle.bz2"
readonly ASN_MAP="${STATS}/nro/asn-cc-best.csv"

python3 create-combined-member-list.py \
    "${NETIXLAN_DUMP}" \
    "../raw-data/lg-dumps/de-cix-fra-member-asns.csv" \
    "${ASN_MAP}" \
    31 \
    "${STATS}/peeringdb/de-cix-fra-combined-member-asns.csv"

python3 create-combined-member-list.py \
    "${NETIXLAN_DUMP}" \
    "../raw-data/lg-dumps/ix-br-sp-member-asns.csv" \
    "${ASN_MAP}" \
    171 \
    "${STATS}/peeringdb/ix-br-sp-combined-member-asns.csv"