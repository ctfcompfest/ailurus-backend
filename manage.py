import importlib
from pathlib import Path
import sys

args = sys.argv[1:]


def help():
    print("Usage: python manage.py [module] [args]")
    print("Available modules:")
    for path in Path(__file__).parent.iterdir():
        if path.is_file():
            continue

        if path.joinpath("main.py").exists():
            print(f" - {path.name}")


if __name__ == "__main__":
    if len(args) < 1:
        help()
        exit()

    module_name = args[0]
    module_args = args[1:]

    try:
        module = importlib.import_module(f"{module_name}.main")
        module.main(module_args)
    except ModuleNotFoundError:
        help()
        exit()
