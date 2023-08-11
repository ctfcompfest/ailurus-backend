from dotenv import load_dotenv

load_dotenv()

from flask import Flask
from and_platform.models import db, migrate
from and_platform.api import api_blueprint
from and_platform.api.auth import bp as auth_blueprint
from and_platform.api.contest import bp as contest_blueprint
from and_platform.api.flag import bp as flag_blueprint
from and_platform.api.services import bp as service_blueprint
from and_platform.checker import main as checker_main
from typing import List


def manage(args: List[str]):
    if len(args) < 1:
        return

    if args[1] == "checker":
        return checker_main(args[1:])

    # TODO: Other commands


def create_app():
    app = Flask(
        __name__,
        static_url_path="/static",
        static_folder="static",
    )
    app.config.from_prefixed_env()

    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Blueprints
    app.register_blueprint(api_blueprint)
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(contest_blueprint)
    app.register_blueprint(flag_blueprint)
    app.register_blueprint(service_blueprint)

    return app
