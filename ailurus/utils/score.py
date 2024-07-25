from ailurus.models import Challenge, Team, Flag

def calculate_submission_score(attacker: Team, defender: Team, challenge: Challenge, flag: Flag):
    return 1.0