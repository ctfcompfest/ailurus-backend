from ailurus.models import Service
from ailurus.utils.config import get_app_config
from ailurus.svcmodes.rootuser_aws.schema import ServiceManagerTask

import os
import zipfile
import base64

def init_artifact(body, **kwargs):
    chall_id = body["challenge_id"]
    artifactroot_folder = os.path.join(get_app_config("DATA_DIR"), "..", "worker_data", "artifacts")
    artifact_folder = os.path.join(artifact_folder, f"artifact-{chall_id}")
    artifact_zipfile = os.path.join(artifactroot_folder, f"artifact-{chall_id}.zip")
    
    os.makedirs(artifactroot_folder, exist_ok=True)
    with open(artifact_zipfile, 'wb') as fp:
        fp.write(base64.b64decode(body["artifact"]))
    with zipfile.ZipFile(artifact_zipfile, "r") as fp:
        fp.extractall(artifact_folder)

def do_provision(body: ServiceManagerTask, **kwargs):
    init_artifact(body, **kwargs)    
    # TODO:

def do_restart(body: ServiceManagerTask, **kwargs):
    init_artifact(body, **kwargs)    
    # TODO:

def do_reset(body: ServiceManagerTask, **kwargs):
    init_artifact(body, **kwargs)    
    # TODO:
