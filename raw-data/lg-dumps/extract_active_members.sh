#!/bin/bash
set -euo pipefail

python3 extract_active_members.py de-cix.20230315.raw.pickle.bz2 de-cix-fra-member-asns.csv
python3 extract_active_members.py ix-br.20230315.raw.pickle.bz2 ix-br-sp-member-asns.csv
python3 extract_active_members.py linx.20230315.raw.pickle.bz2 linx-lon1-member-asns.csv
