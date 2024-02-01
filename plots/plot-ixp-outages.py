from datetime import datetime, timezone

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd

OUT_FILE_TYPE = '.pdf'
BIN_DIR = '../stats/ixp-outages/'
FIGS_DIR = '../figs/ixp-outages/'


def plot(data: pd.DataFrame,
         params: dict):
    fig, ax = plt.subplots()

    ax.fill_between('bin_timestamp',
                    0,
                    'target_ix',
                    data=data,
                    label='Target ✔ / IXP ✔',
                    color='#0571b0',
                    )
    ax.fill_between('bin_timestamp',
                    'target_ix',
                    'target_no_ix',
                    data=data,
                    label='Target ✔ / IXP ✗',
                    color='#92c5de',
                    )
    ax.fill_between('bin_timestamp',
                    'target_no_ix',
                    'no_target_ix',
                    data=data,
                    label='Target ✗ / IXP ✔',
                    color='#f4a582',
                    )
    ax.fill_between('bin_timestamp',
                    'no_target_ix',
                    'no_target_no_ix',
                    data=data,
                    label='Target ✗ / IXP ✗',
                    color='#ca0020',
                    )
    ax.legend(ncol=2,
              bbox_to_anchor=(0.5, 1),
              loc='lower center',
              )
    ax.set_ylim(0, 100)
    ax.set_ylabel('Traceroutes (%)')

    ax.xaxis.set_major_locator(ticker.MultipleLocator(7200))
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(
        lambda x, pos: f'{datetime.fromtimestamp(x, tz=timezone.utc).strftime("%H")}h'))
    ax.tick_params('x', labelsize='small')

    if 'xlabel' in params:
        ax.set_xlabel(params['xlabel'])

    if 'type' in params and params['type'] == 'amsix':
        ax.set_xlim(datetime(2015, 5, 13, 7, 30, tzinfo=timezone.utc).timestamp(),
                    datetime(2015, 5, 13, 18, 0, tzinfo=timezone.utc).timestamp())
    if 'type' in params and params['type'] == 'decix':
        ax.set_xlim(datetime(2018, 4, 9, 13, 30, tzinfo=timezone.utc).timestamp(),
                    datetime(2018, 4, 10, 14, 0, tzinfo=timezone.utc).timestamp())
    if 'type' in params and params['type'] == 'linx':
        ax.set_xlim(datetime(2021, 3, 23, 7, 30, tzinfo=timezone.utc).timestamp(),
                    datetime(2021, 3, 24, 2, 30, tzinfo=timezone.utc).timestamp())
    if 'type' in params and params['type'] == 'amsix2023':
        ax.set_xlim(datetime(2023, 11, 22, 12, 30, tzinfo=timezone.utc).timestamp(),
                    datetime(2023, 11, 23, 15, 0, tzinfo=timezone.utc).timestamp())
    if 'outfile' in params:
        plt.savefig(params['outfile'], bbox_inches='tight')


def to_pct(data: pd.DataFrame):
    data['target_ix'] = data['target_ix'] / data['num_tr'] * 100
    data['target_no_ix'] = data['target_ix'] + data['target_no_ix'] / data['num_tr'] * 100
    data['no_target_ix'] = data['target_no_ix'] + data['no_target_ix'] / data['num_tr'] * 100
    data['no_target_no_ix'] = data['no_target_ix'] + data['no_target_no_ix'] / data['num_tr'] * 100


def plot_amsix():
    data = pd.read_csv(f'{BIN_DIR}amsix.result-bins.2015-05-13.csv')
    to_pct(data)
    plot(data, {
        'xlabel': '2015-05-13 (UTC)',
        'type': 'amsix',
        'outfile': f'{FIGS_DIR}amsix{OUT_FILE_TYPE}',
    })


def plot_decix():
    data = pd.concat([pd.read_csv(f'{BIN_DIR}decix.result-bins.2018-04-09.csv'),
                      pd.read_csv(f'{BIN_DIR}decix.result-bins.2018-04-10.csv')])
    to_pct(data)
    plot(data, {
        'xlabel': '2018-04-09/10 (UTC)',
        'type': 'decix',
        'outfile': f'{FIGS_DIR}decix{OUT_FILE_TYPE}',
    })


def plot_linx():
    data = pd.concat([pd.read_csv(f'{BIN_DIR}linx.result-bins.2021-03-23.csv'),
                      pd.read_csv(f'{BIN_DIR}linx.result-bins.2021-03-24.csv')])
    to_pct(data)
    plot(data, {
        'xlabel': '2021-03-23/24 (UTC)',
        'type': 'linx',
        'outfile': f'{FIGS_DIR}linx{OUT_FILE_TYPE}',
    })


def plot_amsix_2023():
    data = pd.read_csv(f'{BIN_DIR}amsix.result-bins.2023-11-22.csv')
    to_pct(data)
    plot(data, {
        'xlabel': '2023-11-22/23 (UTC)',
        'type': 'amsix2023',
        'outfile': f'{FIGS_DIR}/amsix2023{OUT_FILE_TYPE}',
    })


def plot_all():
    plot_amsix()
    plot_decix()
    plot_linx()
    plot_amsix_2023()


if __name__ == '__main__':
    plot_all()
