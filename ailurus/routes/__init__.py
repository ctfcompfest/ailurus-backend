from ailurus.utils.config import get_config
from ailurus.routes.api import api_blueprint
from ailurus.models import db, Config
from flask import Blueprint, redirect, render_template, request
from typing import List, Tuple

app_routes = Blueprint("main", __name__)
app_routes.register_blueprint(api_blueprint)

@app_routes.get("/")
def index():
    if not get_config("ADMIN_SECRET"):
        return redirect("/setup")
    return redirect("/api/ping")

@app_routes.get("/setup")
def setup_page():
    if get_config("ADMIN_SECRET"):
        return redirect("/")
    return render_template("admin/setup.html")

@app_routes.post("/setup")
def setup_post():
    if get_config("ADMIN_SECRET"):
        return redirect("/")

    admin_secret_cfg = Config(
        key="ADMIN_SECRET",
        value=request.form.get("ADMIN_SECRET", "insecure-admin1234")
    )
    db.session.add(admin_secret_cfg)

    configs: List[Tuple[Config]] = db.session.execute(db.select(Config)).fetchall()
    for config_tuple in configs:
        config = config_tuple[0]
        cfg_form_val = request.form.get(config.key)
        if cfg_form_val:
            config.value = cfg_form_val
    
    db.session.commit()

    return "Configuration Applied!"