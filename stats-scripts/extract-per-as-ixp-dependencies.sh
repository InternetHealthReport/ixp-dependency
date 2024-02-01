#!/bin/bash
set -euo pipefail

readonly STATS="../stats"
readonly ASN_MAP="${STATS}/nro/asn-cc-best.csv"

for F in "${STATS}"/hegemony/*hegemony.csv; do
    BASE=$(basename -s .hegemony.csv "${F}")
    PER_SCOPE="${STATS}/per-scope-interfaces/${BASE}.per_scope_interfaces.csv.bz2"
    echo "${F}"
    echo "${PER_SCOPE}"
    if [ ! -f "${PER_SCOPE}" ]; then
        echo "No per-scope interfaces found. Skipping."
        continue
    fi
    python3 ./extract-per-as-ixp-dependencies.py \
        "${F}" \
        "${PER_SCOPE}" \
        "${ASN_MAP}" \
        "${STATS}/per-as-ixp-dependencies/"
done

