import argparse
import sys

import pandas as pd

INPUT_FILE = '../stats/peeringdb/20221006-ixp.csv'
OUTPUT_FILE = '../stats/peeringdb/20221006-valid-ixps.csv'
DATA_DELIMITER = ','


def main() -> None:
    desc = """Create a list of ix_id that are valid for our analysis.
    For now these are only IXPs with at least two IPv4 members."""
    parser = argparse.ArgumentParser(description=desc)
    args = parser.parse_args()

    ixps = pd.read_csv(INPUT_FILE)
    ixps[ixps.peers_v4 > 1].id.to_csv(OUTPUT_FILE, header=False, index=False)


if __name__ == '__main__':
    main()
    sys.exit(0)
