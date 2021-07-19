import logging
from pathlib import Path
from argparse import ArgumentParser

from . import __version__
from .config import current_config


cli = ArgumentParser()
cli.add_argument('--version', action='version', version=f"%(prog)s {__version__}")
cli.add_argument('--config', action='store', metavar='FILE', help='path to configuration file', default='config.py')
cli.add_argument('-v', '--verbose', action='count', default=0, help='verbosity')
subparsers = cli.add_subparsers(dest="subcommand")


def argument(*name_or_flags, **kwargs):
    """Convenience function to properly format arguments to pass to the
    subcommand decorator.
    """

    return (list(name_or_flags), kwargs)


def subcommand(args=[], parent=subparsers):
    """Decorator to define a new subcommand in a sanity-preserving way.
    The function will be stored in the ``func`` variable when the parser
    parses arguments so that it can be called directly like so::
        args = cli.parse_args()
        args.func(args)
    Usage example::
        @subcommand([argument("-d", help="Enable debug mode", action="store_true")])
        def subcommand(args):
            print(args)
    Then on the command line::
        $ python cli.py subcommand -d
    """

    def decorator(func):
        parser = parent.add_parser(func.__name__, description=func.__doc__)
        for arg in args:
            parser.add_argument(*arg[0], **arg[1])
        parser.set_defaults(func=func)

    return decorator


def main():
    """Main entrypoint function, dispatching subcommands.
    """

    args = cli.parse_args()
    if args.subcommand is None:
        cli.print_help()
        return 1

    else:
        # Set up logger
        levels = [logging.WARNING, logging.INFO, logging.DEBUG]
        level = levels[min(len(levels) - 1, args.verbose)]
        logging.basicConfig(
            level=level,
            format='%(asctime)-15s %(levelname)8s [%(name)s] %(message)s',
        )

        # Load config
        config_path = Path(args.config)
        if config_path.exists():
            current_config.load_from_file(config_path)

        # Call subcommand
        return args.func(args)
