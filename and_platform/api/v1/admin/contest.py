from and_platform.models import db, Configs
from flask import Blueprint, jsonify, request, views
from sqlalchemy import select

contest_blueprint = Blueprint("contest", __name__, url_prefix="/contest")

class ContestConfig(views.MethodView):
    def get(self):
        configs = db.session.execute(select(Configs)).all()
        response = {cfg[0].key:cfg[0].value for cfg in configs}
        return jsonify(status="success", data=response)

    def put(self):
        print(request.headers.get("x-adce-secret"))
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
        
        return jsonify(status="success", data=response)

contest_blueprint.add_url_rule('/config', view_func=ContestConfig.as_view('contest_config'))