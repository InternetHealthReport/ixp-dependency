#!/bin/bash
set -euo pipefail

readonly STATS="../stats"
readonly IXP_PEERS="${STATS}/peeringdb/20221006-ixp-peers.csv"

for F in "${STATS}"/per-as-ixp-dependencies/*per_as_ixp_dependencies.csv; do
    echo "${F}"
    python3 ./get-new-country-count.py \
        "${IXP_PEERS}" \
        "${F}" \
        "${STATS}/new-country-count/"
done

