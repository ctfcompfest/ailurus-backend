from flask_socketio import SocketIO
from ailurus.models import Team, Challenge

socketio = SocketIO(logger=True, cors_allowed_origins="*")


def send_attack_event(
    attacker: Team, defender: Team, challenge: Challenge, is_first_blood: bool = False, solved_at: str = "N/A"
):
    attacker_dict = {
        "id": attacker.id,
        "name": attacker.name,
    }
    defender_dict = {
        "id": defender.id,
        "name": defender.name,
    }
    challenge_dict = {
        "id": challenge.id,
        "name": challenge.title,
    }
    socketio.emit(
        "attack-event",
        {
            "attacker": attacker_dict,
            "defender": defender_dict,
            "challenge": challenge_dict,
            "first_blood": is_first_blood,
            "solved_at": solved_at,
        },
    )
