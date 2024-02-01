#!/bin/bash
set -euo pipefail

readonly STATS="../stats"
readonly PDB_REGIONALITY="${STATS}/ixp-regionality/20221006-ixp_pdb_regionality.csv"
readonly FIGS="../figs/peer-regionality-scatter/"

for F in "${STATS}"/ixp-table/*.ixp_table.csv; do
    python3 ./plot-peer-regionality-scatter.py "${F}" "${PDB_REGIONALITY}" "${FIGS}"
done

