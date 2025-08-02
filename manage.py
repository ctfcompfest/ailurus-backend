from ailurus import create_keeper_daemon, create_worker_daemon, create_webapp_daemon

import argparse
import flask_migrate
import sys
import os

# Ensure the script directory is in the system path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Manage script for running Ailurus Backend services.')
    subparser = parser.add_subparsers(dest="command", help='subcommand help')

    webapp_parser = subparser.add_parser('webapp', help='webapp command help')
    webapp_parser.add_argument('--host', type=str, help='the interface web app will bind to.')
    webapp_parser.add_argument('--port', type=int, help='the port web app will bind to.')

    checker_parser = subparser.add_parser('checker', help='worker command help')
    flagrotator_parser = subparser.add_parser('flagrotator', help='worker command help')
    svcmanager_parser = subparser.add_parser('svcmanager', help='worker command help')
    keeper_parser = subparser.add_parser('keeper', help='keeper command help')
    
    args = sys.argv[1:]
    if len(args) < 1:
        parser.print_help()
        exit()

    user_arg = parser.parse_args(args)
    if user_arg.command == 'webapp':
        webapp_opts = {
            'host': vars(user_arg)['host'] or '0.0.0.0',
            'port': vars(user_arg)['port'] or 5000
        }

        webapp = create_webapp_daemon()

        with webapp.app_context():
            flask_migrate.upgrade()

        socketio = webapp.extensions['socketio']
        socketio.run(webapp, log_output=True, **webapp_opts)
    elif user_arg.command == 'keeper':
        create_keeper_daemon()
    elif user_arg.command == 'checker':
        create_worker_daemon('checker')
    elif user_arg.command == 'svcmanager':
        create_worker_daemon('svcmanager')
    elif user_arg.command == 'flagrotator':
        create_worker_daemon('flagrotator')
