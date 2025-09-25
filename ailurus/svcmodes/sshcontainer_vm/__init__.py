from ailurus.svcmodes.migrations import upgrade

from .checker import handler_checker_task
from .flagrotator import handler_flagrotator_task
from .services import generator_public_services_info, generator_public_services_status_detail
from .svcmanager import handler_svcmanager_request, handler_svcmanager_task

import flask

def load(app: flask.Flask):
    upgrade()
