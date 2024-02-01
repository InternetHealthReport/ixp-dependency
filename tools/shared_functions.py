from datetime import datetime, timezone
from typing import Tuple

import matplotlib.pyplot as plt

# Thresholds are inclusive (≤)
SMALL_AS_THRESHOLD = 2
MEDIUM_AS_THRESHOLD = 180
SMALL_IX_THRESHOLD = 2
MEDIUM_IX_THRESHOLD = 180
NO_DEPS_MARKER = '2'
SMALL_IX_MARKER = '*'
MEDIUM_IX_MARKER = 'o'
LARGE_IX_MARKER = '^'
COLORS = {'no_deps': '#ef3b2c',
          'small': '#6baed6',
          'medium': '#2171b5',
          'large': '#08306b',
          'as': '#e41a1c',
          'ixp': '#377eb8'}
COLOR_FILL = {'small': '#ffeda0',
              'medium': '#feb24c',
              'large': '#f03b20'}


def convert_date_to_epoch(s) -> int:
    """Parse date from config file with format %Y-%m-%dT%H:%M and return
    it as a UNIX epoch in seconds.

    Return 0 if the date can not be parsed."""
    try:
        return int(datetime.strptime(s, "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc).timestamp())
    except ValueError:
        # Not a valid date.
        return 0


def parse_timestamp_argument(arg: str) -> int:
    """Parse a timestamp argument which can either be given as a UNIX
    epoch in seconds or milliseconds, or as a date with format
    %Y-%m-%dT%H:%M and return it as a UNIX epoch in seconds.

    Return 0 if the timestamp can not be parsed."""
    if arg is None:
        return 0
    if arg.isdigit():
        if len(arg) == 10:
            # Already epoch in seconds.
            return int(arg)
        elif len(arg) == 13:
            # Epoch in milliseconds.
            return int(arg) // 1000
        # Invalid format.
        return 0
    return convert_date_to_epoch(arg)


def sanitize_dir(dir: str) -> str:
    if not dir.endswith('/'):
        return f'{dir}/'
    return dir


def annotate(id_label: str,
             annotation_label: str,
             text_offset: Tuple[float, float],
             id_list: list,
             x: list,
             y: list,
             ax: plt.Axes,
             x_offset: float = 0,
             y_offset: float = 0) -> None:
    if id_label not in id_list:
        return
    idx = id_list.index(id_label)
    ax.annotate(annotation_label,
                (x[idx] + x_offset, y[idx] + y_offset),
                text_offset,
                textcoords='offset points',
                arrowprops={'arrowstyle': '->'})


def read_to_set(input_file: str) -> set:
    """Return set consisting of stripped lines from the input file."""
    with open(input_file, 'r') as f:
        return {line.strip() for line in f}
