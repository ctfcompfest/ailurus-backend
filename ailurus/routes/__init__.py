from ailurus.utils.config import get_config
from ailurus.routes.api import api_blueprint
from ailurus.models import db, Config, ManageServiceUnlockMode
from flask import Blueprint, redirect, render_template, request, url_for
from typing import List

import ailurus.svcmodes
import json
import os

app_routes = Blueprint("main", __name__)
app_routes.register_blueprint(api_blueprint)

@app_routes.get("/")
def index():
    if not get_config("ADMIN_SECRET"):
        return redirect(url_for("main.setup_page"))
    return redirect(url_for('main.api.ping'))

@app_routes.get("/setup")
def setup_page():
    if get_config("ADMIN_SECRET"):
        return redirect(url_for('main.index'))

    svcmode_dir = os.path.dirname(ailurus.svcmodes.__file__)
    service_modes = []
    for elm in os.listdir(svcmode_dir):
        realpath = os.path.join(svcmode_dir, elm)
        cfgfile_path = os.path.join(realpath, "config.json")
        if not os.path.isdir(realpath) or \
            not os.path.exists(cfgfile_path): continue
        with open(cfgfile_path) as cfgfile:
            cfg = json.load(cfgfile)
            service_modes.append({
                "id": elm,
                "display": cfg["display"],
            })
    return render_template("admin/setup.html", unlock_modes = ManageServiceUnlockMode, service_modes = service_modes)

@app_routes.post("/setup")
def setup_submit():
    if get_config("ADMIN_SECRET"):
        return redirect(url_for('main.index'))

    admin_secret_cfg = Config(
        key="ADMIN_SECRET",
        value=request.form.get("ADMIN_SECRET", "insecure-admin1234")
    )
    db.session.add(admin_secret_cfg)

    configs: List[Config] = Config.query.all()
    for config in configs:
        cfg_form_val = request.form.get(config.key)
        if cfg_form_val:
            config.value = cfg_form_val
    
    db.session.commit()

    return "Configuration Applied!"