#!/bin/bash
set -euo pipefail

readonly STATS="../stats"
readonly ASN_CC="${STATS}/nro/asn-cc-best.csv"
readonly IXP_INFO="${STATS}/peeringdb/20221006-ixp.csv"

for F in "${STATS}"/hegemony/*hegemony.csv; do
    echo "${F}"
    python3 ./compute-ixp-regionality.py \
        "${F}" \
        "${ASN_CC}" \
        "${IXP_INFO}" \
        "${STATS}/ixp-regionality/"
done

