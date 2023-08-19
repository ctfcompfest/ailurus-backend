from pathlib import Path
from typing import TypedDict
from flask import current_app
import yaml


class ChallengeData(TypedDict):
    title: str
    description: str
    num_expose: int


def get_challenges_directory():
    data_dir = Path(current_app.config.get("DATA_DIR", ""))
    path = data_dir.joinpath("challenges")
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_challenge(challenge_id: str) -> ChallengeData:
    config_path = get_challenges_directory().joinpath(
        "chall-" + challenge_id, "challenge.yaml"
    )
    with open(config_path, "r") as f:
        return yaml.safe_load(f.read())
