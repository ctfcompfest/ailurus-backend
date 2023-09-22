from flask_socketio import SocketIO
from and_platform.models import Teams

socketio = SocketIO(logger=True)

def send_attack_event(attacker: Teams, defender: Teams):
    attacker_dict = {
        "id": attacker.id,
        "name": attacker.name,
    }
    defender_dict = {
        "id": defender.id,
        "name": defender.name,
    }
    socketio.emit('attack event', {'attacker': attacker_dict, 'defender': defender_dict})