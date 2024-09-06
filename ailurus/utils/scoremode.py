import ailurus.scoremodes
import importlib
import os


def get_scoremode_module(scoremode: str):
    scoremode_dir = os.path.dirname(ailurus.scoremodes.__file__)
    package_dir = os.path.join(scoremode_dir, scoremode)
    
    spec = importlib.util.spec_from_file_location(
        f"ailurus.scoremodes.{scoremode}",
        os.path.join(package_dir, "__init__.py")
    )
    
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    return mod
