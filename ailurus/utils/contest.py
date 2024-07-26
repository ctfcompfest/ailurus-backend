from ailurus.models import (
    Flag,
    Team,
    Challenge,
)
from ailurus.utils.config import get_config
from secrets import choice
from string import ascii_lowercase, digits

def calculate_submission_score(attacker: Team, defender: Team, challenge: Challenge, flag: Flag):
    return 1.0

def generate_flag(current_round: int, current_tick: int, team: Team, challenge: Challenge, order: int = 0) -> Flag:
    CHARSET = ascii_lowercase + digits
    flag_format = get_config("FLAG_FORMAT")
    flag_rndlen = get_config("FLAG_RNDLEN", 0)
    
    flag_format = flag_format.replace("__ROUND__", str(current_round))
    
    SUBRULE = {
        "__TEAM__": str(team.id),
        "__PROBLEM__": str(challenge.id),
        "__RANDOM__": "".join([choice(CHARSET) for _ in range(flag_rndlen)]),
    }
    new_flag = flag_format
    for k, v in SUBRULE.items():
        new_flag = new_flag.replace(k, v)
            
    return Flag(
        team_id = team.id,
        challenge_id = challenge.id,
        round = current_round,
        tick = current_tick,
        value = new_flag,
        order = order
    )
