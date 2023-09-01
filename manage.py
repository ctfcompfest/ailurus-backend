from and_platform import create_scheduler, create_app, create_checker, create_checker_executor, create_contest_worker
from multiprocessing import Process
import sys
import argparse

args = sys.argv[1:]

def help():
    print("Usage: python manage.py [module] [args]\n")
    print("Available modules: checker, web")

def run_web(argv):
    flask_app = create_app()
    celery_schedule = create_scheduler(flask_app)
    celery_worker = create_contest_worker(flask_app)
    Process(target=celery_schedule.start, args=(["beat", "-l", "info"],)).start()
    Process(target=celery_worker.start, args=(["worker", "-l", "info"],)).start()
    flask_app.run()

def run_checker():
    celery = create_checker()
    celery.start(["worker", "-E", "--loglevel", "INFO"])
    
def run_checker_executor(**kwargs):
    checker = create_checker_executor()
    checker.run_check(kwargs['team'], kwargs['challenge'])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='PROG')
    subparser = parser.add_subparsers(dest="command", help='subcommand help')

    checkexec_parser = subparser.add_parser('checkexec', help='checker executor command help')
    checkexec_parser.add_argument('--team', type=int, required=True, help="team id")
    checkexec_parser.add_argument('--challenge', type=int, required=True, help="challenge id")

    checker_parser = subparser.add_parser('checker', help='checker command help')
    web_parser = subparser.add_parser('web', help='web command help')

    if len(args) < 1:
        parser.print_help()
        exit()

    user_arg = parser.parse_args(args)
    if user_arg.command == "checkexec":
        run_checker_executor(**vars(user_arg))
    elif user_arg.command == "checker":
        run_checker()
    elif user_arg.command == "web":
        run_web(user_arg)
    else:
        help()    
