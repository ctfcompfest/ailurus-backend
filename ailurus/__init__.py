from ailurus.models import db, migrate, Team
from ailurus.routes import app_routes
from ailurus.utils.cors import CORS
from ailurus.worker.keeper import create_keeper
from and_platform.api import api_blueprint
from and_platform.cache import cache
from and_platform.socket import socketio
from dotenv import load_dotenv
from flask import Flask
from flask_jwt_extended import JWTManager

import datetime
import os
import sqlalchemy

def setup_jwt_app(app: Flask):
    app.config["JWT_SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")
    app.config["JWT_ALGORITHM"] = "HS512"
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(hours=12)
    jwt = JWTManager(app)

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        return db.session.execute(
            sqlalchemy.select(Team).filter(Team.id == identity["team"]["id"])
        ).scalar()


def init_data_dir(app):
    app.config["TEMPLATE_DIR"] = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "templates"
    )
    if not app.config.get("DATA_DIR"):
        app.config["DATA_DIR"] = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), ".adce_data"
        )

    for d in ["challenges", "services"]:
        dirpath = os.path.join(app.config["DATA_DIR"], d)
        os.makedirs(dirpath, exist_ok=True)

def create_app(env_file=".env"):
    load_dotenv(env_file, override=True)
    
    app = Flask(
        __name__,
        static_url_path="/static",
        static_folder="static",
    )

    with app.app_context():
        app.config.from_prefixed_env()

        db.init_app(app)
        migrate.init_app(app, db)
        cache.init_app(app)

        socketio.init_app(app)
        setup_jwt_app(app)
        # create_keeper(app)
        CORS(app)

        try:
            init_data_dir(app)
        except Exception as e:
            # To detect that the relation has not been created yet
            app.logger.warning("Error calling some function while create_app %s", e)

        # Blueprints
        app.register_blueprint(api_blueprint)
        app.register_blueprint(app_routes)
        
    return app