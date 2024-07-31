import logging

from .schema import FlagrotatorTask

log = logging.getLogger(__name__)

rootflag_path = "/etc/root/flag.txt"
userflag_path = "/home/ubuntu/flag.txt"

def handler_flagrotator_task(body: FlagrotatorTask, **kwargs):
    pass

    # TODO: process this
