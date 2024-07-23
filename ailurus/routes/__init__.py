from ailurus.utils.config import get_config
from ailurus.routes.api import api_blueprint
from ailurus.models import db, Config
from flask import Blueprint, redirect, render_template, request, url_for
from typing import List

app_routes = Blueprint("main", __name__)
app_routes.register_blueprint(api_blueprint)

@app_routes.get("/")
def index():
    if not get_config("ADMIN_SECRET"):
        return redirect(url_for("main.setup_page"))
    return redirect(url_for('api.ping'))

@app_routes.get("/setup")
def setup_page():
    if get_config("ADMIN_SECRET"):
        return redirect(url_for('main.index'))
    return render_template("admin/setup.html")

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