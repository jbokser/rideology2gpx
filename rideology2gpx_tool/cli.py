from click import command, option, argument, Choice
from click import Path as TypePath
from click import DateTime as TypeDateTime
from click.exceptions import UsageError
from datetime import datetime
from pathlib import Path
from tabulate import tabulate
from .main import main
from .app_info import app_info, version



dt_formats = ['%Y-%m-%d %H:%M:%S']
dt_str_default = datetime.now().strftime(dt_formats[0])


def dinamic_help_decorator(**wildcards):
    def fnc(f):
        doc = f.__doc__
        for key, value in wildcards.items():
            doc = doc.replace('{' + key + '}', value)
        f.__doc__ = doc
        return f
    return fnc

filter_options = [
        'from-0-to-100-kmh',
        'from-20-to-120-kmh',
        'from-100-to-200-kmh',
        'from-100-to-top-speed',
        'from-120-to-top-speed',
        'from-0-to-top-speed',
        'from-60-to-top-speed',
        'chop-1km-at-end',
        'chop-1km-at-start',
        'chop-1km-at-start-and-end',
        'chop-3km-at-end',
        'chop-3km-at-start',
        'chop-3km-at-start-and-end'
    ]
def filter_options_str():
    opts = filter_options[:]
    opts_row = ['']
    opts_table = []
    while opts:
        opts_row.append(opts.pop(0))
        if len(opts_row)==4:
            opts_table.append(opts_row)
            opts_row = ['']
    if opts_row:
        opts_table.append(opts_row)
    return tabulate(opts_table, tablefmt='plain')

epilog = f"""\b
The valid values ​for FILTER are:
{filter_options_str()}
"""

@command(context_settings=dict(help_option_names=['-h', '--help']),
         epilog=epilog)
@option('-v', '--version', 'show_version', is_flag=True,
    help='Show version and exit.')
@option('-d', '--date', 'start_time',
        type=TypeDateTime(formats=dt_formats),
        default=dt_str_default,
        help='Starting datetime for the track in the GPX files.')
@option('-f', '--filter', 'data_filter',
        type=Choice(filter_options, case_sensitive=False),
        metavar='FILTER',
        help='Filter applied to waypoints.')
@argument('csv_file', type=TypePath(), required=False)
@argument('output_dir', type=TypePath(), required=False)
@option('-g', '--graph', 'graph', is_flag=True,
    help='Make graphs and md report.')
@dinamic_help_decorator(**app_info)
def cli(csv_file, output_dir, start_time,
        show_version=False, data_filter=None, graph=None):
    """
    A simple command line program to transform log files obtained with the
    Kawasaki Rideology App into GPX files.

    \b
    CSV_FILE - File obtained with the Kawasaki Rideology App.
    OUTPUT_DIR - Optional output directory where the files will be created.

    \b
    For more info: {repo_url}
    Author: {author} <{author_email}> 
    Version: {version}
    """

    if show_version:
        print(version)
        return

    if output_dir is not None:
        output_dir = Path(output_dir)
        if not output_dir.is_dir():
            raise UsageError(
                "Error: argument 'OUTPUT_DIR' is not a directory.")          

    if csv_file is None:
        raise UsageError("Error: Missing argument 'CSV_FILE'.")
    
    min_speed = None
    max_speed = None
    ending_chop = 0
    starting_chop = 0
    subtitle = ''
    out_filename_suffix = ''

    if data_filter == 'from-0-to-100-kmh':
        min_speed = 0
        max_speed = 100
        subtitle = 'from stop to 100 km/h'
        out_filename_suffix='(0-100kmh)'

    elif data_filter == 'from-20-to-120-kmh':
        min_speed = 20
        max_speed = 120
        subtitle = 'from 20 km/h to 100 km/h'
        out_filename_suffix='(20-120kmh)'

    elif data_filter == 'from-100-to-200-kmh':
        min_speed = 100
        max_speed = 200
        subtitle = 'from 100 km/h to 200 km/h'
        out_filename_suffix='(100-200kmh)'

    elif data_filter == 'from-0-to-top-speed':
        min_speed = 0
        subtitle = 'from stop to top speed'
        out_filename_suffix='(0-top-kmh)'

    elif data_filter == 'from-60-to-top-speed':
        min_speed = 60
        subtitle = 'from 60 km/h to top speed'
        out_filename_suffix='(60-top-kmh)'

    elif data_filter == 'from-100-to-top-speed':
        min_speed = 100
        subtitle = 'from 100 km/h to top speed'
        out_filename_suffix='(100-top-kmh)'

    elif data_filter == 'from-120-to-top-speed':
        min_speed = 120
        subtitle = 'from 120 km/h to top speed'
        out_filename_suffix='(120-top-kmh)'

    elif data_filter == 'chop-1km-at-end':
        ending_chop = 1
        out_filename_suffix='chop'

    elif data_filter == 'chop-1km-at-start':
        starting_chop = 1
        out_filename_suffix='chop'

    elif data_filter == 'chop-1km-at-start-and-end':
        ending_chop = 1
        starting_chop = 1
        out_filename_suffix='chop'

    elif data_filter == 'chop-3km-at-end':
        ending_chop = 3
        out_filename_suffix='chop'

    elif data_filter == 'chop-1km-at-start':
        starting_chop = 3
        out_filename_suffix='chop'

    elif data_filter == 'chop-3km-at-start-and-end':
        ending_chop = 3
        starting_chop = 3
        out_filename_suffix='chop'

    main(
        csv_file,
        output_dir = output_dir,
        silent=False,
        start_time=start_time,
        min_speed = min_speed,
        max_speed = max_speed,
        ending_chop = ending_chop,
        starting_chop = starting_chop,
        subtitle = subtitle,
        do_graph = graph,
        out_filename_suffix = out_filename_suffix
    )
