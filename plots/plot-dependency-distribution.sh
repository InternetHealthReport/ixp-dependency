#!/bin/bash
set -euo pipefail

readonly STATS="../stats/hegemony"
readonly VALID_IXPS="../stats/peeringdb/20221006-valid-ixps.csv"
readonly FIGS="../figs/dependency-distribution/"

for F in "${STATS}"/*.hegemony.csv; do
    python3 ./plot-dependency-distribution.py "${F}" "${VALID_IXPS}" "${FIGS}"
done

