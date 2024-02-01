#!/bin/bash
set -euo pipefail

readonly STATS="../stats"
readonly FIGS="../figs/per-as-ixp-dependencies"
readonly ARK="${STATS}/per-as-ixp-dependencies/ark.2022-09-19.per_as_ixp_dependencies.csv"
readonly IXP_INFO="${STATS}/peeringdb/20221006-ixp.csv"

python3 ./plot-ixp-country-as-dependency-bars.py \
    "${ARK}" \
    "${IXP_INFO}" \
    "${FIGS}"
