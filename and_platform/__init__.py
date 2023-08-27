import datetime
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()

from flask import Flask
from flask_jwt_extended import JWTManager
from and_platform.models import Teams, db, migrate
from and_platform.api import api_blueprint
from and_platform.api.auth import bp as auth_blueprint
from and_platform.api.contest import bp as contest_blueprint
from and_platform.api.flag import bp as flag_blueprint
from and_platform.api.services import bp as service_blueprint
from and_platform.checker import main as checker_main
from and_platform.core.config import get_config, set_config
from typing import List

import os
import sqlalchemy


def setup_jwt_app(app: Flask):
    jwt = JWTManager(app)

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        return db.session.execute(
            sqlalchemy.select(Teams).filter(Teams.id == identity["team"]["id"])
        ).scalar()


def manage(args: List[str]):
    if len(args) < 1:
        return

    if args[1] == "checker":
        return checker_main(args[1:])

    # TODO: Other commands

def init_data_dir(app):
    app.config["TEMPLATE_DIR"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
    if not app.config.get("DATA_DIR"):
        app.config["DATA_DIR"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".adce_data")

    for d in ["challenges", "services"]:
        dirpath = os.path.join(app.config["DATA_DIR"], d)
        os.makedirs(dirpath, exist_ok=True)

def load_adce_config():
    # If config already exists in database, it will not follow .env
    for key, value in os.environ.items():
        realkey = key[5:]
        if not key.startswith("ADCE_") or get_config(realkey) != None:
            continue
        set_config(realkey, value)


def create_app():
    app = Flask(
        __name__,
        static_url_path="/static",
        static_folder="static",
    )

    with app.app_context():
        app.config.from_prefixed_env()

        # Extensions
        CORS(app, origins=[
            "https://ctf.compfest.id",
            "http://127.0.0.1:3000",
            "http://localhost:3000",
            "http://localhost"
        ])
        db.init_app(app)
        migrate.init_app(app, db)

        app.config["JWT_SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")
        app.config["JWT_ALGORITHM"] = "HS512"
        app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(hours=12)
        setup_jwt_app(app)

        try:
            load_adce_config()
            init_data_dir(app)
        except sqlalchemy.exc.ProgrammingError:
            # To detect that the relation has not been created yet
            app.logger.warning("Error calling some function while create_app")

        # Blueprints
        app.register_blueprint(api_blueprint)
        app.register_blueprint(auth_blueprint)
        app.register_blueprint(contest_blueprint)
        app.register_blueprint(flag_blueprint)
        app.register_blueprint(service_blueprint)

    return app
