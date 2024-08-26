from ailurus.svcmodes.migrations import upgrade

from .checker import handler_checker_task, generator_public_services_status_detail
from .leaderboard import get_leaderboard
from .flagrotator import handler_flagrotator_task
from .svcmanager import generator_public_services_info, handler_svcmanager_request, handler_svcmanager_task
from .routes import checker_agent_blueprint

import flask

def load(app: flask.Flask):
    upgrade("lksn24")
    app.register_blueprint(checker_agent_blueprint)
