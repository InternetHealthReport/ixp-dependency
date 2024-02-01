#!/bin/bash
set -u

readonly STATS="../stats"
readonly IXP_INFO="${STATS}/peeringdb/20221006-ixp.csv"
readonly IXP_PEERS="${STATS}/peeringdb/20221006-ixp-peers.csv"
readonly ASN_CC_MAP="${STATS}/nro/asn-cc-best.csv"

for HEGEMONY in "${STATS}"/hegemony/*hegemony.csv; do
    BASE=$(basename -s .hegemony.csv "${HEGEMONY}")
    INTERFACES="${STATS}/interfaces/${BASE}.interfaces.csv"
    echo "${BASE}"
    python3 ./compute-ixp-table.py \
        "${IXP_INFO}" \
        "${IXP_PEERS}" \
        "${INTERFACES}" \
        "${HEGEMONY}" \
        "${ASN_CC_MAP}" \
        "${STATS}/ixp-table/"
done
