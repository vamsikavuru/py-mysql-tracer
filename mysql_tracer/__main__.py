import argparse
import logging

from mysql_tracer import _configuration
from mysql_tracer._cursor_provider import CursorProvider
from mysql_tracer._query import Query

log = logging.getLogger('mysql_tracer')


def get_main_args_parser(parents, defaults):
    description = 'CLI script to run queries and export results.'

    parser = argparse.ArgumentParser(parents=parents,
                                     description=description,
                                     formatter_class=argparse.RawTextHelpFormatter)

    parser.set_defaults(**{
        'port': 3306,
        **defaults
    })

    query = parser.add_argument_group(title='Queries')
    query.add_argument('query', nargs='+', help='Path to a file containing a single sql statement')
    query.add_argument('-t', '--template-var', dest='template_vars', nargs=2, metavar=('KEY', 'VALUE'),
                       action='append',
                       help='Define a key value pair to substitute the ${key} by the value within the query')

    db = parser.add_argument_group(title='Database')
    db.add_argument('--host', required=True, help='MySQL server host')
    db.add_argument('--port', type=int, help='MySQL server port')
    db.add_argument('--user', required=True, help='MySQL database user')
    db.add_argument('--database', help='MySQL database name')

    pwd = parser.add_argument_group(title='Password')
    pwd.add_argument('-a', '--ask-password', action='store_true',
                     help='Ask password; do not try to retrieve password from keyring')
    pwd.add_argument('-s', '--store-password', action='store_true',
                     help='Store password into keyring after connecting to the database')

    export = parser.add_argument_group(title='Export')
    excl_actions = export.add_mutually_exclusive_group()
    excl_actions.add_argument('-d', '--destination', help='Directory where to export results')
    excl_actions.add_argument('--display', action='store_true', help='Do not export results but display them to stdout')

    # noinspection PyProtectedMember
    for action in parser._actions:
        if action.required and action.default is not None:
            action.required = False

    return parser


def get_log_args_parser():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
    # log_args, remaining_args = log_args_parser.parse_known_args()

    # if log_args.log_level is not None:
    #     configure_logger(log_args.log_level)

    return parser


def configure_logger(log_level):
    log.setLevel(log_level)
    console = logging.StreamHandler()
    console.setLevel(log_level)
    console.setFormatter(logging.Formatter(fmt='%(asctime)s %(levelname)s - %(name)s: %(message)s'))
    log.addHandler(console)


def main():
    log_args_parsers = get_log_args_parser()
    log_args, remaining_args = log_args_parsers.parse_known_args()

    if log_args.log_level:
        configure_logger(log_args.log_level)

    config = _configuration.get()

    main_args_parser = get_main_args_parser([log_args_parsers], config)
    main_args = main_args_parser.parse_args()

    if not log_args.log_level and main_args.log_level:
        configure_logger(main_args.log_level)

    CursorProvider.init(main_args.host, main_args.user, main_args.port, main_args.database, main_args.ask_password,
                        main_args.store_password)

    template_vars = main_args.template_vars if main_args.template_vars else []
    queries = [Query(path, dict(template_vars)) for path in main_args.query]

    for query in queries:
        if main_args.display:
            query.display()
        else:
            query.export(destination=main_args.destination)


if __name__ == '__main__':
    main()
