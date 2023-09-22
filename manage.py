from and_platform import create_scheduler, create_app, create_checker, create_checker_executor, create_contest_worker
from and_platform.socket import socketio
from multiprocessing import Process, cpu_count
from wsgi import StandaloneApplication
import sys
import argparse

WSGI_OPTS = {
    "workers": (cpu_count()) + 1,
    "worker_class": "sync",
}

args = sys.argv[1:]

def help():
    print("Usage: python manage.py [module] [args]\n")
    print("Available modules: checker, web")

def run_web(**kwargs):
    flask_app = create_app()
    
    flask_arg = {
        'debug': kwargs.get('host') or False,
        'host': kwargs.get('host') or '0.0.0.0',
        'port': kwargs.get('port') or 5000,
    }
    socketio.run(flask_app, **flask_arg)


def run_webcelery(**kwargs):
    flask_app = create_app()
    celery_schedule = create_scheduler(flask_app)
    celery_worker = create_contest_worker(flask_app)

    if kwargs['debug']:
        celery_extra_opts = ['--loglevel', "DEBUG"]

        Process(target=celery_schedule.start, args=(["beat"] + celery_extra_opts,)).start()
        celery_worker.start(["worker"] + celery_extra_opts).start()
    else:
        celery_extra_opts = ['--loglevel', "INFO"]
        
        Process(target=celery_schedule.start, args=(["beat"] + celery_extra_opts,)).start()
        celery_worker.start(["worker", "-E"] + celery_extra_opts).start()
 

def run_checker(**kwargs):
    celery_extra_opts = []
    celery_extra_opts = ['--loglevel', "INFO"]
    celery = create_checker()
    celery.start(["worker", "-E"] + celery_extra_opts)
    
def run_checker_executor(**kwargs):
    checker = create_checker_executor()
    checker.run_check(kwargs['team'], kwargs['challenge'])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='PROG')
    subparser = parser.add_subparsers(dest="command", help='subcommand help')

    checkexec_parser = subparser.add_parser('checkexec', help='checker executor command help')
    checkexec_parser.add_argument('--team', type=int, required=True, help="specify service team id.")
    checkexec_parser.add_argument('--challenge', type=int, required=True, help="specify service challenge id.")

    checker_parser = subparser.add_parser('checker', help='checker command help')
    checker_parser.add_argument('--debug', action='store_true', help='turn on debug mode.')

    web_parser = subparser.add_parser('web', help='web command help')
    web_parser.add_argument('--debug', action='store_true', help='turn on debug mode.')
    web_parser.add_argument('--host', type=str, help='the interface web app will bind to.')
    web_parser.add_argument('--port', type=int, help='the port web app will bind to.')

    webcelery_parser = subparser.add_parser('webcelery', help='web celery command help')
    webcelery_parser.add_argument('--debug', action='store_true', help='turn on debug mode.')
    webcelery_parser.add_argument('--host', type=str, help='the interface web app will bind to.')
    webcelery_parser.add_argument('--port', type=int, help='the port web app will bind to.')

    if len(args) < 1:
        parser.print_help()
        exit()

    user_arg = parser.parse_args(args)
    if user_arg.command == "checkexec":
        run_checker_executor(**vars(user_arg))
    elif user_arg.command == "checker":
        run_checker(**vars(user_arg))
    elif user_arg.command == "web":
        run_web(**vars(user_arg))
    elif user_arg.command == "webcelery":
        run_webcelery(**vars(user_arg))
    else:
        help()    
