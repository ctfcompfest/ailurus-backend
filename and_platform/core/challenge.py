from pathlib import Path
from typing import Optional, TypedDict
from flask import current_app
import yaml


class ChallengeData(TypedDict):
    name: str
    description: str
    num_expose: int
    server_id: Optional[int]


def get_challenges_directory():
    data_dir = Path(current_app.config.get("DATA_DIR", ""))
    path = data_dir.joinpath("challenges")
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_challenges_dir_fromid(challenge_id: str):
    return get_challenges_directory().joinpath("chall-" + challenge_id)

def load_challenge(challenge_id: str) -> ChallengeData:
    config_path = get_challenges_dir_fromid(challenge_id).joinpath(
        "challenge.yml"
    )
    with open(config_path, "r") as f:
        return yaml.safe_load(f.read())
