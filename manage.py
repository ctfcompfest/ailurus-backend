from ailurus import create_keeper_daemon, create_worker_daemon, create_webapp_daemon
from gevent import monkey

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
    webapp_parser.add_argument('--spawn', type=int, help='the number of web app worker need to be spawn.')

    migrator_parser = subparser.add_parser('migrate', help='migrate command help')
    worker_parser = subparser.add_parser('worker', help='worker command help')
    keeper_parser = subparser.add_parser('keeper', help='keeper command help')
    
    args = sys.argv[1:]
    if len(args) < 1:
        parser.print_help()
        exit()

    user_arg = parser.parse_args(args)
    if user_arg.command == 'webapp':
        webapp_opts = {
            'host': vars(user_arg)['host'] or '0.0.0.0',
            'port': vars(user_arg)['port'] or 5000,
            'spawn': vars(user_arg)['spawn'] or 10
        }

        webapp = create_webapp_daemon()
        socketio = webapp.extensions['socketio']

        monkey.patch_all()
        socketio.run(webapp, log_output=True, **webapp_opts)
    elif user_arg.command == 'migrate':
        webapp = create_webapp_daemon()
        with webapp.app_context():
            flask_migrate.upgrade()
    elif user_arg.command == 'keeper':
        create_keeper_daemon()
    elif user_arg.command == 'worker':
        create_worker_daemon()