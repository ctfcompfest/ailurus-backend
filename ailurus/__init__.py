import dotenv.parser
from ailurus.models import db, migrate, Team
from ailurus.routes import app_routes
from ailurus.utils.cors import CORS
from ailurus.utils.security import limiter
from ailurus.utils.socket import socketio
from ailurus.worker import create_keeper, create_worker
from flask import Flask
from flask_jwt_extended import JWTManager

import dotenv
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
    env_var = dotenv.dotenv_values(env_file)
    
    app = Flask(
        __name__,
        static_url_path="/static",
        static_folder="static",
    )

    with app.app_context():
        app.config.from_prefixed_env()
        app.config.from_mapping(env_var)

        # Data
        db.init_app(app)
        migrate.init_app(app, db)
        init_data_dir(app)

        # Security
        setup_jwt_app(app)
        CORS(app)
        limiter.init_app(app)
        
        # Socket
        socketio.init_app(app)

        # API
        app.register_blueprint(app_routes)

        # Keeper
        create_keeper(app)
        
    return app

def create_worker_daemon(env_file=".env.worker"):
    configs = dotenv.dotenv_values(env_file)
    create_worker(**configs)
