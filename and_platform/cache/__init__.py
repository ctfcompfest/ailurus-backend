from flask_caching import Cache

cache = Cache()

def clear_public_challenge():
    from and_platform.models import ChallengeReleases
    from and_platform.api.v1.challenge import get_all_challenge, get_challenge_by_id

    cache.delete_memoized(get_all_challenge)
    cache.delete_memoized(get_challenge_by_id)
    cache.delete_memoized(ChallengeReleases.get_challenges_from_round)

def clear_public_team():
    from and_platform.api.v1.teams import get_all_teams, get_team_by_id

    cache.delete_memoized(get_all_teams)
    cache.delete_memoized(get_team_by_id)

def clear_config():
    from and_platform.core.config import _get_config

    cache.delete_memoized(_get_config)
    