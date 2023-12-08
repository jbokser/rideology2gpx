from click import command, option, argument
from click import Path as TypePath
from click.exceptions import UsageError
from .app_info import version, author, author_email, repo_url


def dinamic_help_decorator(f):
    doc = f.__doc__
    doc = doc.replace('{version}', version)
    doc = doc.replace('{author}', author)
    doc = doc.replace('{author_email}', author_email)
    doc = doc.replace('{repo_url}', repo_url)
    f.__doc__ = doc
    return f


@command(context_settings=dict(help_option_names=['-h', '--help']))
@option('-v', '--version', 'show_version', is_flag=True,
    help='Show version and exit.')
@argument('csv_file', type=TypePath(), required=False)
@dinamic_help_decorator
def cli(csv_file, show_version=False):
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
    
    print("""This app is still in development.
Work in progress!!!.
See the develop branch in the repository.""")
    