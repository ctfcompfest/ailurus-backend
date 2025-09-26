from datetime import datetime
from ailurus.models import db
from ailurus.models import Service

from ..types import ServiceManagerTaskType
from .container import run_container, restart_container, delete_container, restart_container, prepare_container


import logging

log = logging.getLogger(__name__)


def do_provision(body: ServiceManagerTaskType, **kwargs):
    team_id = body["team_id"]
    chall_id = body["challenge_id"]
    artifact_checksum = body["artifact_checksum"]
    
    existing_service = Service.query.filter_by(
        team_id=team_id,
        challenge_id=chall_id,
    ).first()
    if existing_service:
        log.info(f"Service for team_id={team_id}, chall_id={chall_id} exist.")
        return False    
    try:
        service = prepare_container(team_id, chall_id, artifact_checksum)
        db.session.add(service)
        db.session.flush()
        
        run_container(team_id, chall_id, artifact_checksum)
        
        db.session.commit()
        log.info(f"Successfully provision service for team_id={team_id}, chall_id={chall_id}")
    except Exception as e:
        log.error(e)
        db.session.rollback()
        log.info(f"Failed provision service for team_id={team_id}, chall_id={chall_id}")

    

def do_delete(body: ServiceManagerTaskType, **kwargs):
    team_id = body["team_id"]
    chall_id = body["challenge_id"]
    
    delete_container(team_id, chall_id)
    
    service: Service = Service.query.filter_by(
        team_id=team_id,
        challenge_id=chall_id,
    ).first()
    if not service:
        raise ValueError(f"Service for team_id={team_id}, chall_id={chall_id} not found")
    
    db.session.delete(service)
    db.session.commit()
    log.info(f"Successfully delete service for team_id={team_id}, chall_id={chall_id}")
    
    
def do_reset(body: ServiceManagerTaskType, **kwargs):
    team_id = body["team_id"]
    chall_id = body["challenge_id"]
    
    delete_container(team_id, chall_id)
    run_container(team_id, chall_id, body["artifact_checksum"])
    log.info(f"Successfully reset service for team_id={team_id}, chall_id={chall_id}")
    

def do_restart(body: ServiceManagerTaskType, **kwargs):
    team_id = body["team_id"]
    chall_id = body["challenge_id"]
    
    restart_container(team_id, chall_id)
    log.info(f"Successfully restart service for team_id={team_id}, chall_id={chall_id}")
    