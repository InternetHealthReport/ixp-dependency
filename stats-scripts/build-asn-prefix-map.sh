#!/bin/bash
set -euo pipefail

DELEGATED_STATS="../raw-data/20221006-delegated-stats.bz2"
RIB_FILE="../raw-data/rib.20221001.pickle.bz2"
OUT="../stats/nro/asn-prefix-map-best.pickle.bz2"
OUT_CC="../stats/nro/asn-cc-best.csv"

python3 ./build-asn-prefix-map.py \
    "$DELEGATED_STATS" \
    "$RIB_FILE" \
    "$OUT" \
    "$OUT_CC"