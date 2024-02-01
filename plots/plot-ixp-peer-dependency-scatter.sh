#!/bin/bash
set -euo pipefail

readonly STATS="../stats/ixp-table"
readonly FIGS="../figs/ixp-peer-dependency-scatter/"

for F in "${STATS}"/*.ixp_table.csv; do
    python3 ./plot-ixp-peer-dependency-scatter.py "${F}" "${FIGS}"
done

