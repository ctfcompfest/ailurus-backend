from and_platform import create_scheduler, create_app, create_checker, create_contest_worker
from multiprocessing import Process
import sys

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

def run_checker(argv):
    celery = create_checker()
    celery.start(["worker"] + argv)

if __name__ == "__main__":
    if len(args) < 1:
        help()
        exit()

    module_name = args[0]
    if module_name == "checker":
        run_checker(args[1:])
    elif module_name == "web":
        run_web(args[1:])
    else:
        help()    
