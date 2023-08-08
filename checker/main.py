from typing import List
from and_platform.app import app
from and_platform.models.core import Team  # Model importing works!


def main(args: List[str]):
    with app.app_context():
        ...
