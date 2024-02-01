#!/bin/bash
set -euo pipefail

readonly STATS="../stats"
readonly ASN_CC="${STATS}/nro/asn-cc-best.csv"
readonly IXP_PEERS="${STATS}/peeringdb/20221006-ixp-peers.csv"
readonly OUTPUT="${STATS}/ixp-regionality/20221006-ixp_pdb_regionality.csv"

    python3 ./compute-ixp-pdb-regionality.py \
        "${IXP_PEERS}" \
        "${ASN_CC}" \
        "${OUTPUT}"
