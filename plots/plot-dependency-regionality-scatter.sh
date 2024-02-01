#!/bin/bash
set -euo pipefail

readonly STATS="../stats/ixp-regionality"
readonly FIGS="../figs/dependency-regionality-scatter/"

for F in "${STATS}"/*.ixp_regionality.csv; do
    python3 ./plot-dependency-regionality-scatter.py "${F}" "${FIGS}"
done

