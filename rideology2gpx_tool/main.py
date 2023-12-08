from sys import stderr, stdout
from datetime import datetime
from .data_file import DataFile


def bye(text=None, code=1):
    if text:
        print(
            (text if code==0 else f"Error, {text}"),
            file=(stdout if code==0 else stderr)
        )
    exit(code)


def main(
        filename = 'example/ride.csv',
        silent=False,
        start_time=None,
        min_speed = None,
        max_speed = None,
        ending_chop = 0,
        starting_chop = 0,
        subtitle = ''
        ):

    datafile = DataFile(filename)

    if start_time is None:
        start_time = datetime.now()

    try:
        datafile.load()
    except FileNotFoundError as e:
        bye(f"file {repr(e.filename)} not found.", 1)
    except IsADirectoryError as e:
        bye(f"{repr(e.filename)} is a directory, not a file.", 1)
    except UnicodeDecodeError as e:
        bye(f"{repr(filename)} is not a CSV file.", 1)

    if not datafile:
        bye(f"no data in file {repr(filename)}.", 2)

    if ending_chop:
        datafile.filter_by_distance(-abs(ending_chop))

    if starting_chop:
        datafile.filter_by_distance(abs(starting_chop))

    if min_speed is not None:
        datafile.filter_by_speed(min_speed, max_speed)

    if subtitle:
        datafile.title = f"{datafile.title}, {subtitle}"

    datafile.dump(show_report=not(silent), silent=silent, start_time=start_time)
