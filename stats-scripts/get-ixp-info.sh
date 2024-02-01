#!/bin/bash
set -euo pipefail

readonly STATS="../stats/peeringdb"

python3 ./get-ixp-info.py \
    "${STATS}/20221006-peeringdb-ixp.pickle.bz2" \
    "${STATS}/20221006-peeringdb-netixlan.pickle.bz2" \
    "${STATS}/20221006-ixp.csv"
