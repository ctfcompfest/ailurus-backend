from flask import Blueprint, render_template
from ailurus.utils.config import get_config

app_routes = Blueprint("main", __name__)

@app_routes.get("/")
def index():
    if not get_config("ADCE_SECRET"):
        return "hai"
    return "done"