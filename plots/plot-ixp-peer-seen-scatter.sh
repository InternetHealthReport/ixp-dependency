#!/bin/bash
set -uo pipefail

readonly STATS="../stats/ixp-table"
readonly FIGS="../figs/ixp-peer-seen-scatter/"

for F in "${STATS}"/*.ixp_table.csv; do
    python3 ./plot-ixp-peer-seen-scatter.py "${F}" "${FIGS}"
done

