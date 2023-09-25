from and_platform.models import db, Configs
from and_platform.cache import clear_config
from flask import Blueprint, jsonify, request, views
from sqlalchemy import select

contest_blueprint = Blueprint("contest", __name__, url_prefix="/contest")

@contest_blueprint.get('/config')
def get_contest_config():
    configs = db.session.execute(select(Configs)).all()
    response = {cfg[0].key:cfg[0].value for cfg in configs}
    return jsonify(status="success", data=response)

@contest_blueprint.put('/config')
def update_contest_config():
    req = request.get_json()
    req_configkey = list(req["configs"].keys())
    configs = db.session.execute(
            select(Configs)
            .where(Configs.key.in_(req_configkey))
        ).all()
    if len(configs) != len(req_configkey):
        return jsonify(status="not found", message="some configuration not found."), 404
    
    response = {}
    for cfg in configs:
        cfg[0].value = req["configs"][cfg[0].key]
        response[cfg[0].key] = cfg[0].value
    db.session.commit()
    
    clear_config()

    return jsonify(status="success", data=response)