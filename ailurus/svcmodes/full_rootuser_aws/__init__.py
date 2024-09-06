from flask import Flask

from .checker import handler_checker_task, generator_public_services_status_detail
from .flagrotator import handler_flagrotator_task
from .svcmanager import generator_public_services_info, handler_svcmanager_request, handler_svcmanager_task

def load(app: Flask):
    pass