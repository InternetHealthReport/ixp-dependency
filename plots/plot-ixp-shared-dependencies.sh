#!/bin/bash
set -euo pipefail

readonly STATS="../stats"
readonly SCOPE_DETAILS="${STATS}/per-as-ixp-dependencies/ark.2022-09-19.per_scope_details.pickle.bz2"
readonly FIGS="../figs/ixp-shared-dependencies/"

if [ ! $# -eq 1 ]; then
    echo "usage: $0 <ix_id>"
    exit 0
fi

IX_ID=$1

python3 plot-ixp-shared-dependencies.py "${SCOPE_DETAILS}" "${IX_ID}" "${FIGS}"