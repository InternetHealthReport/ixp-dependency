import argparse
import bz2
import logging
import pickle
import sys
from collections import defaultdict
from itertools import combinations

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

sys.path.append('..')
from tools.shared_functions import sanitize_dir

DATA_DELIMITER = ','
MIN_ENTRIES = 0
BOLD_THRESHOLD = 10
# Set to True for IX.br or other plots with too many entries.
HIDE_NON_BOLD_ENTRIES = False


def load_ix_data(per_scope_details: str, ix_id: str) -> dict:
    with bz2.open(per_scope_details, 'rb') as f:
        data = pickle.load(f)
    if ix_id not in data:
        logging.error(f'Failed to find IXP with id {ix_id} in data.')
        return dict()
    return data[ix_id]


def make_matrix(cc_data: dict) -> pd.DataFrame:
    m = defaultdict(lambda: defaultdict(int))
    for participant_tuple, scope_list in cc_data.items():
        for p1, p2 in combinations(participant_tuple, 2):
            p1 = int(p1)
            p2 = int(p2)
            m[p1][p2] += len(scope_list)
            m[p2][p1] += len(scope_list)
    df = pd.DataFrame(m)
    df.fillna(0, inplace=True)
    df.sort_index(inplace=True)
    df.sort_index(axis=1, inplace=True)
    return df


def plot_heatmap(data: pd.DataFrame, output_file: str) -> None:
    data_filtered = data[data.astype(bool).sum(axis=1) >= MIN_ENTRIES]
    data_filtered = data_filtered[data_filtered.columns[data_filtered.astype(bool).sum() > 0]]
    bold_index = data_filtered[data_filtered.astype(bool).sum(axis=1) >= BOLD_THRESHOLD].index
    fig, ax = plt.subplots(1, 2,
                           width_ratios=(0.975, 0.025),
                           gridspec_kw={'wspace': 0.05},
                           layout='compressed')
    ax[0].grid(False)
    sns.heatmap(data_filtered,
                xticklabels=True,
                yticklabels=True,
                mask=data_filtered == 0,
                ax=ax[0],
                cbar_ax=ax[1],
                cmap=sns.color_palette("crest", as_cmap=True),
                cbar_kws={'label': '#Shared Dependent ASes'},
                square=True,
                linewidths=0.75,
                linecolor='#DDD',
                vmin=1,
                vmax=26
                )
    ax[0].tick_params(length=0, labelsize='xx-small')
    ax[1].tick_params(length=2, direction='out')
    ylabels = ax[0].get_yticklabels()
    for label in ylabels:
        if int(label.get_text()) in bold_index:
            label.set_fontweight('bold')
        elif HIDE_NON_BOLD_ENTRIES:
            label.set_visible(False)
    xlabels = ax[0].get_xticklabels()
    for label in xlabels:
        if int(label.get_text()) in bold_index:
            label.set_fontweight('bold')
        elif HIDE_NON_BOLD_ENTRIES:
            label.set_visible(False)
    plt.savefig(output_file, bbox_inches='tight')
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('per_scope_details')
    parser.add_argument('ix_id')
    parser.add_argument('output_dir')
    args = parser.parse_args()

    FORMAT = '%(asctime)s %(levelname)s %(message)s'
    logging.basicConfig(
        format=FORMAT,
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    per_scope_details = args.per_scope_details
    ix_id = args.ix_id

    ix_data = load_ix_data(per_scope_details, ix_id)
    if not ix_data:
        sys.exit(1)

    output_dir = sanitize_dir(args.output_dir)

    for cc in ix_data:
        # Remove this to plot for all countries.
        if ix_id == '31' and cc != 'RU' or ix_id == '171' and cc != 'BR':
            continue
        multiples = ix_data[cc]['multiple']
        if not multiples:
            continue
        logging.info(cc)
        output_file_prefix = f'{output_dir}{ix_id}.{cc}'
        matrix = make_matrix(multiples)
        plot_heatmap(matrix, f'{output_file_prefix}.heatmap.pdf')
        matrix_output_file = f'{output_dir}fig-stats/{ix_id}.{cc}.matrix.csv'
        matrix.to_csv(matrix_output_file)


if __name__ == '__main__':
    main()
    sys.exit(0)
