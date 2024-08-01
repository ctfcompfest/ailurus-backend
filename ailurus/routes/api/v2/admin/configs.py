from ailurus.models import db, Config
from ailurus.utils.contest import update_paused_status
from flask import Blueprint, request, jsonify
from typing import List

import json

config_blueprint = Blueprint("config", __name__, url_prefix="/configs")

@config_blueprint.get("/")
def get_configs():
    configs: List[Config] = Config.query.all()
    config_datas = {}
    for config in configs:
        config_datas[config.key] = config.value
    return jsonify(status="success", data=config_datas)

@config_blueprint.patch("/<string:config_key>/")
def update_config(config_key: str):
    config: Config | None = Config.query.filter_by(key=config_key).first()
    if config == None:
        return jsonify(status="not found", message="configuration key not found."), 404

    new_value = request.get_json().get("value")
    if new_value == None:
        return jsonify(status="not found", message="missing 'value' key in body request."), 400
    
    if config_key == "IS_CONTEST_PAUSED":
        update_paused_status(str)

    if not isinstance(new_value, str):
        new_value = json.dumps(new_value)
    config.value = new_value
    db.session.commit()

    return jsonify(status="success", data={"key": config.key, "value": config.value})