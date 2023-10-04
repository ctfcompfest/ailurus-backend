from and_platform.core.config import get_config, check_contest_is_freeze
from and_platform.models import db, ChallengeReleases, Flags, Submissions, Solves, Teams, Challenges
from and_platform.socket import send_attack_event

def submit_flag(team_id: int, flag: str, chall_id: int | None = None):
    current_tick = get_config("CURRENT_TICK", 0)
    current_round = get_config("CURRENT_ROUND", 0)
    chall_releases = ChallengeReleases.get_challenges_from_round(current_round)
    
    new_submission = Submissions(
        team_id=team_id,
        challenge_id=chall_id,
        round=current_round,
        tick=current_tick,
        value=flag,
    )

    flag_found = Flags.query.filter(
        Flags.value == flag,
        Flags.tick == current_tick,
    ).first()
    
    if (flag_found == None) or \
        (flag_found.challenge_id not in chall_releases) or \
        (chall_id != None and chall_id not in chall_releases) or \
        (chall_id != None and flag_found.challenge_id != chall_id):
       new_submission.verdict = False
       db.session.add(new_submission)
       return {"flag": flag, "verdict": "flag is wrong or expired."}
    
    prev_correct_submission = Submissions.query.filter(
        Submissions.flag_id == flag_found.id,
        Submissions.team_id == team_id,
        Submissions.verdict == True,
    ).first()
    # Repeated correct submission will not be logged
    if prev_correct_submission:
       return {"flag": flag, "verdict": "flag already submitted."}

    new_submission.verdict = True
    new_submission.flag_id = flag_found.id
    new_submission.challenge_id = flag_found.challenge_id
    db.session.add(new_submission)

    unlock_mode = get_config("UNLOCK_MODE", "personal")
    prev_solve = Solves.query.filter_by(team_id=team_id, challenge_id=flag_found.challenge_id).first()
    if prev_solve == None:
        if unlock_mode == "personal":
            if flag_found.team_id == team_id:
                solve = Solves(team_id=team_id, challenge_id=flag_found.challenge_id)
                db.session.add(solve)
        else:
            solve = Solves(team_id=team_id, challenge_id=flag_found.challenge_id)
            db.session.add(solve)

    db.session.commit()
    
    # Emit attack event only when attacker and defender is different
    if (flag_found.team_id != team_id) and not check_contest_is_freeze():
        attacker = Teams.query.filter(Teams.id == team_id).first()
        defender = Teams.query.filter(Teams.id == flag_found.team_id).first()
        challenge = Challenges.query.filter(Challenges.id == flag_found.challenge_id).first()
        send_attack_event(attacker, defender, challenge)  

    return {"flag": flag, "verdict": "flag is correct."}