from flask_socketio import SocketIO
from and_platform.models import Teams, Challenges

socketio = SocketIO(logger=True, cors_allowed_origins='*')

def send_attack_event(attacker: Teams, defender: Teams, challenge: Challenges):
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
        "name": challenge.name,
    }
    socketio.emit('attack-event', {'attacker': attacker_dict, 'defender': defender_dict, 'challenge': challenge_dict})