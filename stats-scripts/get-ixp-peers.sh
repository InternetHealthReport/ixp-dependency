#!/bin/bash
set -euo pipefail

readonly STATS="../stats"

python3 ./get-ixp-peers.py \
    "${STATS}/peeringdb/20221006-peeringdb-ixp.pickle.bz2" \
    "${STATS}/peeringdb/20221006-peeringdb-netixlan.pickle.bz2" \
    "${STATS}/nro/asn-cc-best.csv" \
    "${STATS}/peeringdb/20221006-ixp-peers.csv"