from dotenv import load_dotenv

load_dotenv()

from flask import Flask
from flask_jwt_extended import JWTManager
from and_platform.models import db, migrate
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

def manage(args: List[str]):
    if len(args) < 1:
        return

    if args[1] == "checker":
        return checker_main(args[1:])

    # TODO: Other commands

def load_adce_config():
    # If config already exists in database, it will not follow .env
    for key, value in os.environ.items():
        realkey = key[5:]
        if not key.startswith("ADCE_") or get_config(realkey) != None: continue
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
        db.init_app(app)
        migrate.init_app(app, db)

        app.config['JWT_SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
        app.config['JWT_ALGORITHM'] = 'HS512'
        jwt = JWTManager()
        jwt.init_app(app)

        try:
            load_adce_config()
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
