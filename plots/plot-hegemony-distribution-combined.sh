#!/bin/bash
set -euo pipefail

readonly STATS="../stats"
readonly HEGEMONY="${STATS}/hegemony"
readonly ARK="${HEGEMONY}/ark.2022-09-19.hegemony.csv"
readonly ATLAS="${HEGEMONY}/atlas.2022-10-03.hegemony.csv"
readonly VALID_IXPS="${STATS}/peeringdb/20221006-valid-ixps.csv"
readonly OUTPUT_FILE="../figs/hegemony-distribution/combined.hegemony_cdf.pdf"

python3 ./plot-hegemony-distribution-combined.py "${ARK}" "${ATLAS}" "${VALID_IXPS}" "${OUTPUT_FILE}"

