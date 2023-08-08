from typing import List
from and_platform.app import app


def main(args: List[str]):
    with app.app_context():
        ...
