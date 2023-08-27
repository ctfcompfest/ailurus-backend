from pathlib import Path
from typing import List, Optional, TypedDict
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


def check_chall_config(challenge_id: str):
    REQUIRED_PATHS = [
        Path("test/test.py"),
        Path("docker-compose.yml"),
        Path("patchrule.yml"),
    ]
    chall_dir = get_challenges_directory().joinpath("chall-" + challenge_id)

    missing: List[str] = []
    for path in REQUIRED_PATHS:
        if not chall_dir.joinpath(path).exists():
            missing.append(str(path))

    return len(missing) == 0, missing


def write_chall_info(chall: ChallengeData, challenge_id: str):
    config_path = get_challenges_directory().joinpath(
        "chall-" + challenge_id, "challenge.yaml"
    )

    with open(config_path, "w") as f:
        return yaml.safe_dump(chall, f)
