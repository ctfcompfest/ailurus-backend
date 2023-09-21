from flask_caching import Cache

cache = Cache()

def clear_public_challenge():
    from and_platform.models import ChallengeReleases
    from and_platform.api.v1.challenge import get_all_challenge, get_challenge_by_id

    cache.delete_memoized(get_all_challenge)
    cache.delete_memoized(get_challenge_by_id)
    cache.delete_memoized(ChallengeReleases.get_challenges_from_round)
