from dotenv import load_dotenv

load_dotenv()

from flask import Flask
from and_platform.extensions import db, migrate
from and_platform.routes.auth import bp as auth_blueprint
from and_platform.routes.contest import bp as contest_blueprint
from and_platform.routes.flag import bp as flag_blueprint
from and_platform.routes.services import bp as service_blueprint



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
app.register_blueprint(auth_blueprint)
app.register_blueprint(contest_blueprint)
app.register_blueprint(flag_blueprint)
app.register_blueprint(service_blueprint)