import dotenv.parser
from ailurus.models import db, migrate, Team
from ailurus.routes import app_routes
from ailurus.utils.cache import cache
from ailurus.utils.cors import CORS
# from ailurus.utils.security import limiter
from ailurus.utils.socket import socketio
from ailurus.utils.svcmode import load_all_svcmode
from ailurus.worker import create_keeper, create_worker
from flask import Flask
from flask_jwt_extended import JWTManager

import dotenv
import datetime
import os
import sqlalchemy
import time
import logging

def create_logger(logname):
    logging.basicConfig(
        level=logging.INFO, # Set the logging level
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', # Log message format
        datefmt='%Y-%m-%d %H:%M:%S', # Date format
        handlers=[
            logging.FileHandler(logname), # Log to a file
            logging.StreamHandler() # Log to the console
        ]
    )

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

    for d in ["challenges", "services", "logs"]:
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
        app.url_map.strict_slashes = False
        
        # Data
        db.init_app(app)
        migrate.init_app(app, db)
        init_data_dir(app)
    return app

def create_keeper_daemon(env_file=".env"):
    app = create_app(env_file)

    with app.app_context():
        create_logger(os.path.join(app.config["DATA_DIR"], "logs", "keeper.log"))

        # Overwrite configuration from env file
        app.config["KEEPER_ENABLE"] = "true"
        create_keeper(app)

    log = logging.getLogger(__name__)
    log.info('Keeper is running. To exit press CTRL+C')
    try:
        while True:
            time.sleep(30)
    except KeyboardInterrupt:
        return

def create_worker_daemon(env_file=".env"):
    configs = dotenv.dotenv_values(env_file)
    app = create_app(env_file)

    with app.app_context():
        create_logger(os.path.join(app.config["DATA_DIR"], "logs", "worker.log"))

        configs["flask_app"] = app
        # Load all svcmode
        load_all_svcmode(app)

        try:
            create_worker(**configs)
        except KeyboardInterrupt:
            return
    
def create_webapp_daemon(env_file=".env"):
    app = create_app(env_file)
    with app.app_context():
        create_logger(os.path.join(app.config["DATA_DIR"], "logs", "webapp.log"))

        # Security
        setup_jwt_app(app)
        CORS(app)
        cache.init_app(app)
        # limiter.init_app(app)
        
        # Socket
        socketio.init_app(app)

        # API
        app.register_blueprint(app_routes)
        
        # Load all svcmode
        load_all_svcmode(app)

        # Keeper
        create_keeper(app)
    return app