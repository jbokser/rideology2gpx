from click import command, option, argument 
from click import Path as TypePath
from click import DateTime as TypeDateTime
from click import IntRange as TypeIntRange
from click.exceptions import UsageError, BadParameter
from datetime import datetime
from pathlib import Path
from .main import main
from .app_info import app_info, version
from typing import List, Callable



# Input date format
dt_formats: List[str] = ['%Y-%m-%d %H:%M:%S']
dt_str_default: str = datetime.now().strftime(dt_formats[0])


def dinamic_help_decorator(**wildcards) -> Callable:
    """
    Dynamically change the __doc__ of a function by replacing wildcards
    with data
    """
    def fnc(f: Callable) -> Callable:
        doc = f.__doc__
        for key, value in wildcards.items():
            doc = doc.replace('{' + key + '}', value)
        f.__doc__ = doc
        return f
    return fnc


@command(context_settings=dict(help_option_names=['-h', '--help']))
@option('-v', '--version', 'show_version', is_flag=True,
    help='Show version and exit.')
@option('-d', '--date', 'start_time',
        type=TypeDateTime(formats=dt_formats),
        default=dt_str_default,
        help='Starting datetime for the track in the GPX files.')
@argument('csv_file', type=TypePath(), required=False)
@argument('output_dir', type=TypePath(), required=False)
@option('-g', '--graph', 'graph', is_flag=True,
    help='Make graphs and md report.')
@option('-s', '--starting-chop', 'starting_chop',
        type=TypeIntRange(0, 10), default=0,
        help='Cut the first X kilometres.', metavar="X")
@option('-e', '--ending-chop', 'ending_chop',
        type=TypeIntRange(0, 10), default=0,
        help='Cut the last X kilometres.', metavar="X")
@option('-a', '--acceleration', 'acceleration',
        type=(str, str), metavar="MIN_SPEED MAX_SPEED",
        help="Filters waypoints to only what is included between the speeds.")
@dinamic_help_decorator(**app_info)
def cli(csv_file, output_dir, start_time,
        show_version=False, graph=None, ending_chop=0,
        starting_chop=0, acceleration=None):
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
    
    if acceleration is not None:

        min_speed, max_speed = [
            str(x).lower().strip() for x in list(acceleration)]
        
        try:
            min_speed = int(min_speed)
        except ValueError:
            raise BadParameter('MIN_SPEED must be integer')
        if min_speed < 0:
            raise BadParameter('MIN_SPEED < 0')
        if min_speed > 400:
            raise BadParameter('MIN_SPEED > 400')

        try:
            max_speed = int(max_speed)
        except ValueError:
            if max_speed in ['top', 'max']:
                max_speed = None
            else:
                raise BadParameter(
                    "MAX_SPEED must be integer or the 'top' wildcard")
        if max_speed is not None:
            if max_speed < 0:
                raise BadParameter('MAX_SPEED < 0')
            if max_speed > 400:
                raise BadParameter('MAX_SPEED > 400')

    subtitle = ''
    out_filename_suffix = []

    if min_speed is not None:

        str_min_speed = f"{min_speed} km/h" if min_speed else 'stop'
        str_max_speed = f"{max_speed} km/h" if max_speed else 'top speed'

        subtitle = f"from {str_min_speed} to {str_max_speed}"

        str_min_speed = f"{min_speed}"
        str_max_speed = f"{max_speed}kmh" if max_speed else 'top-kmh'
        
        out_filename_suffix.append(f"{str_min_speed}-{str_max_speed}")   
    
    if ending_chop or starting_chop:
        out_filename_suffix.append('chop')

    out_filename_suffix = '(' + '-'.join(out_filename_suffix) + ')'
    
    main(
        csv_file,
        output_dir = output_dir,
        silent = False,
        start_time=start_time,
        min_speed = min_speed,
        max_speed = max_speed,
        ending_chop = ending_chop,
        starting_chop = starting_chop,
        subtitle = subtitle,
        do_graph = graph,
        out_filename_suffix = out_filename_suffix
    )
