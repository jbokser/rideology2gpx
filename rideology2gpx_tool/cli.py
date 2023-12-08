from click import command, option, argument, Choice, ClickException, BadParameter
from click import Path as TypePath
from click import DateTime as TypeDateTime
from click.exceptions import UsageError
from datetime import datetime
from .main import main
from .app_info import version, author, author_email, repo_url

dt_formats = ['%Y-%m-%d %H:%M:%S']
dt_str_default = datetime.now().strftime(dt_formats[0])


def dinamic_help_decorator(f):
    doc = f.__doc__
    doc = doc.replace('{version}', version)
    doc = doc.replace('{author}', author)
    doc = doc.replace('{author_email}', author_email)
    doc = doc.replace('{repo_url}', repo_url)
    f.__doc__ = doc
    return f

filter_options = [
        'From-zero-to-100-kmh',
        'From-20-to-120-kmh',
        'From-100-to-200-kmh',
        'From-zero-to-max-speed',
        'Chop-1km-at-end',
        'Chop-1km-at-start',
        'Chop-1km-at-start-and-end',
        'Chop-3km-at-end',
        'Chop-3km-at-start',
        'Chop-3km-at-start-and-end'
    ]

filter_options_str = "\n".join([ f"   {o}" for o in filter_options ])
epilog = f"""\b
The valid values ​​for FILTER are:
{filter_options_str}
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
@dinamic_help_decorator
def cli(csv_file, start_time, show_version=False, data_filter=None):
    """
    A simple command line program to transform log files obtained with the
    Kawasaki Rideology App into GPX files.
    
    \b
    For more info: {repo_url}
    Author: {author} <{author_email}> 
    Version: {version}
    """

    if show_version:
        print(version)
        return
    
    if csv_file is None:
        raise UsageError("Error: Missing argument 'CSV_FILE'.")
    
    min_speed = None
    max_speed = None
    ending_chop = 0
    starting_chop = 0
    subtitle = ''

    if data_filter == 'From-zero-to-100-kmh':
        min_speed = 0
        max_speed = 100
        subtitle = 'from stop to 100 km/h'

    elif data_filter == 'From-20-to-120-kmh':
        min_speed = 20
        max_speed = 120
        subtitle = 'from 20 km/h to 100 km/h'

    elif data_filter == 'From-100-to-200-kmh':
        min_speed = 100
        max_speed = 200
        subtitle = 'from 100 km/h to 200 km/h'

    elif data_filter == 'From-zero-to-max-speed':
        min_speed = 0
        subtitle = 'from stop to max speed'

    elif data_filter == 'Chop-1km-at-end':
        ending_chop = 1

    elif data_filter == 'Chop-1km-at-start':
        starting_chop = 1

    elif data_filter == 'Chop-1km-at-start-and-end':
        ending_chop = 1
        starting_chop = 1

    elif data_filter == 'Chop-3km-at-end':
        ending_chop = 3

    elif data_filter == 'Chop-1km-at-start':
        starting_chop = 3

    elif data_filter == 'Chop-3km-at-start-and-end':
        ending_chop = 3
        starting_chop = 3

    main(
        csv_file,
        silent=False,
        start_time=start_time,
        min_speed = min_speed,
        max_speed = max_speed,
        ending_chop = ending_chop,
        starting_chop = starting_chop,
        subtitle = subtitle
    )
