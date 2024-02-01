import argparse
import logging
import os
import sys
from collections import defaultdict, namedtuple

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

sys.path.append('../')
from tools.shared_functions import sanitize_dir

INPUT_FILE_SUFFIX = '.per_as_ixp_dependencies.csv'
OUTPUT_FILE_SUFFIX = '.pdf'
DATA_DELIMITER = ','
PLOT_TOP = 10

IxpInfo = namedtuple('IxpInfo', 'name name_long cc')


def load_values(input_file: str) -> np.ndarray:
    ix_per_cc = defaultdict(lambda: defaultdict(lambda: {'single': list()}))
    with open(input_file, 'r') as f:
        f.readline()
        for line in f:
            line_split = line.strip().split(DATA_DELIMITER)
            cc = line_split[1]
            if cc == 'overview':
                continue
            ix_id = line_split[0]
            asn = line_split[2]
            scopes = int(line_split[3])
            asn_count = int(line_split[4])
            interface_count = int(line_split[5])
            value = (scopes, asn_count, interface_count)
            if asn in ('general', 'unknown', 'mixed', 'multiple'):
                ix_per_cc[ix_id][cc][asn] = value
            else:
                ix_per_cc[ix_id][cc]['single'].append((asn, *value))
    ix_cc_sortable = dict()
    for ix_id, per_cc_data in ix_per_cc.items():
        cc_list = list()
        for cc, cc_data in per_cc_data.items():
            cc_list.append((cc, cc_data['general'][0], cc_data))
        cc_list.sort(key=lambda t: t[1], reverse=True)
        ix_cc_sortable[ix_id] = cc_list

    return ix_cc_sortable


def read_ixp_info(ixp_info_file: str) -> dict:
    ret = dict()
    with open(ixp_info_file, 'r') as f:
        f.readline()
        for line in f:
            line_split = line.strip().split(DATA_DELIMITER)
            ix_id = line_split[0]
            name = line_split[2]
            name_long = line_split[3]
            cc = line_split[4]
            ret[ix_id] = IxpInfo(name, name_long, cc)
    return ret


def plot_ixp(ix_id: str, values: dict, ixp_info: dict, output_dir: str) -> None:
    ix_info = ixp_info[ix_id]
    ix_data = values[ix_id]
    output_file = f'{output_dir}{ix_id}_' \
                  f'{ix_info.name.replace(" ", "_").replace("/", "_")}' \
                  f'{OUTPUT_FILE_SUFFIX}'

    # fig_height = 0.3 * len(ix_data['general-country'])
    # mpl.rcParams['figure.figsize'] = (6.4, fig_height)
    mpl.rcParams['axes.grid.axis'] = 'x'
    mpl.rcParams['ytick.left'] = False
    fig, ax = plt.subplots()
    y_labels = list()
    bars_plotted = 0
    color_cycle = ('#984ea3', '#ff7f00')
    for y_idx, (cc, general_scope_count, cc_data) in enumerate(ix_data):
        y_labels.append(cc)
        unknown_scope_counts = [('unknown', cc_data['unknown']),
                                ('mixed', cc_data['mixed']), ('multiple', cc_data['multiple'])]
        per_as_scope_counts = list()
        for asn, scope_count, asn_count, interface_count in cc_data['single']:
            per_as_scope_counts.append((asn, scope_count))
        per_as_scope_counts.sort(key=lambda t: t[1], reverse=True)
        plot_data = unknown_scope_counts + per_as_scope_counts

        prev_x = 0
        cycle_idx = 0
        single_ases = 0
        single_scopes = 0
        multiple_ases = 0
        multiple_scopes = 0
        for asn, scope_count in plot_data:
            if asn in ('unknown', 'mixed', 'multiple'):
                # In this case scope_count is actually a tuple as
                # defined by
                # value = (scopes, asn_count, interface_count)
                if asn == 'unknown':
                    hatch = ''
                elif asn == 'mixed':
                    hatch = '//'
                else:
                    multiple_scopes = scope_count[0]
                    multiple_ases = scope_count[1]
                    hatch = 'xxx'
                scope_count = scope_count[0]
                bar = ax.barh(y_idx, scope_count, left=prev_x,
                              color='#4daf4a', hatch=hatch, edgecolor='black', lw=0)
            else:
                single_ases += 1
                single_scopes += scope_count
                cycle_idx = int(not bool(cycle_idx))
                color = color_cycle[cycle_idx]
                bar = ax.barh(y_idx, scope_count, left=prev_x, color=color)
                if ix_id == '31' and cc != '**':
                    if asn == '9498':
                        ax.bar_label(bar, ('9498',),
                                    label_type='center',
                                    fontsize=10)
                    elif asn == '31133':
                        ax.bar_label(bar, ('31133',),
                                    label_type='center',
                                    fontsize=10,
                                    color='white')
                    elif asn == '20485':
                        ax.bar_label(bar, ('20485',),
                                    label_type='center',
                                    fontsize=10)

            prev_x += scope_count
        # ax.annotate(f'{multiple_scopes}/{multiple_ases} {single_scopes}/{single_ases}',
        #             (prev_x, y_idx),
        #             (1, 0),
        #             textcoords='offset points',
        #             va='center')
        ax.annotate(f'{multiple_ases}/{single_ases}',
                    (prev_x, y_idx),
                    (1, 0),
                    textcoords='offset points',
                    va='center')
        bars_plotted += 1
        if bars_plotted == PLOT_TOP:
            break

    ax.set_yticks(np.arange(len(y_labels)), labels=y_labels)
    ax.set_ylabel('Country')
    ax.invert_yaxis()

    ax.set_xlabel('#Dependent ASes')
    # if ix_id == '31':
    #     ax.set_xlim(0, 440)
    #     ax.xaxis.set_major_locator(ticker.MultipleLocator(100))
    #     ax.xaxis.set_minor_locator(ticker.MultipleLocator(50))
    # elif ix_id == '171':
    #     ax.set_xlim(0, 240)
    #     ax.xaxis.set_major_locator(ticker.MultipleLocator(50))
    #     ax.xaxis.set_minor_locator(ticker.MultipleLocator(25))

    # ax.set_title(f'{ix_id} - {ix_info.name} - {ix_info.cc}')
    plt.savefig(output_file, bbox_inches='tight')
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file')
    parser.add_argument('ixp_info_file')
    parser.add_argument('output_dir')
    args = parser.parse_args()

    FORMAT = '%(asctime)s %(levelname)s %(message)s'
    logging.basicConfig(
        format=FORMAT,
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    input_file = args.input_file
    output_dir = sanitize_dir(args.output_dir)

    logging.info(f'Input file: {input_file}')

    ix_info = read_ixp_info(args.ixp_info_file)
    values = load_values(input_file)

    os.makedirs(output_dir, exist_ok=True)
    for ix_id in values:
        if ix_id != '31' and ix_id != '171':
            continue
        plot_ixp(ix_id, values, ix_info, output_dir)


if __name__ == '__main__':
    main()
    sys.exit(0)
