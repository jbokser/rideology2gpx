from sys import stderr, stdout
from datetime import datetime
from .data_file import DataFile
from pathlib import Path


def bye(text=None, code=1) -> None:
    """
    Replacement of exit() function
    """
    if text:
        print(
            (text if code==0 else f"Error, {text}"),
            file=(stdout if code==0 else stderr)
        )
    exit(code)


def main(
        filename = 'example/ride.csv',
        output_dir = None,
        silent = False,
        start_time = None,
        min_speed = None,
        max_speed = None,
        ending_chop = 0,
        starting_chop = 0,
        subtitle = '',
        do_graph = False,
        out_filename_suffix = ''
        ) -> None:

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

    if len(datafile)<=1:
        bye(f"not enough data in the file {repr(filename)}.", 2)

    if subtitle:
        datafile.title = f"{datafile.title}, {subtitle}"

    basename = datafile.filename.stem

    if out_filename_suffix:
        basename = Path(f"{basename}_{out_filename_suffix}").stem

    datafile.dump(
        basename=basename,
        silent=silent,
        start_time=start_time,
        output_dir=output_dir)
    
    if do_graph:
        datafile.dump_md(
            basename=basename,
            silent=silent,
            start_time=start_time,
            output_dir=output_dir)
    
    if not silent:
        print(datafile.report)
