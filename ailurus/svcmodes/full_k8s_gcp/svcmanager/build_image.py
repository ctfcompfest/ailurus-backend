from ailurus.utils.config import get_config
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from os import PathLike

from ..schema import ServiceManagerTaskSchema

import docker
import logging
import os

log = logging.getLogger(__name__)

def do_build_image(body: ServiceManagerTaskSchema, **kwargs):
    challenge_slug = body["challenge_slug"]

    creds_json = get_config("GCP_SERVICE_ACCOUNTS_CREDS", {})
    project_id = creds_json['project_id']
    project_zone = get_config("GCP_ZONE", "us-central1")
    event_slug = get_config("GCP_RESOURCES_PREFIX", "ailurus")    
    image_name_prefix = f"{project_zone}-docker.pkg.dev/{project_id}/{event_slug}-image-artifact"

    challenge_artifact_checksum = body["artifact_checksum"]
    challenge_artifact_path = kwargs["artifact_folder"]
    service_image_name = f"{image_name_prefix}/{challenge_slug}:{challenge_artifact_checksum}"

    challenge_testcase_checksum = body["testcase_checksum"]
    challenge_testcase_path = kwargs["testcase_folder"]
    agentchecker_image_name = f"{image_name_prefix}/{challenge_slug}-agent-checker:{challenge_testcase_checksum}"

    if not get_config("GCP_USE_CLOUD_BUILD", False):
        local_build_image(challenge_artifact_path, service_image_name, creds_json)
        local_build_image(challenge_testcase_path, agentchecker_image_name, creds_json)
    else:
        gcp_build_image(challenge_artifact_path, service_image_name, creds_json)
        gcp_build_image(challenge_testcase_path, agentchecker_image_name, creds_json)

def get_gcp_access_token(service_account_creds: dict) -> str:
    credentials = service_account.Credentials.from_service_account_info(
        info=service_account_creds,
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials.refresh(Request())
    return credentials.token

def local_build_image(artifact_dir: PathLike, image_name: str, service_account_creds: dict):      
    docker_client = docker.from_env()
    try:
        image, build_logs = docker_client.images.build(
            path=artifact_dir,
            dockerfile=os.path.join(artifact_dir, "Dockerfile"),
            tag=image_name,
            rm=True  # Remove intermediate containers after a successful build
        )
        
        # for build_out in build_logs:
        #     if 'stream' in build_out:
        #         log.debug("build-image: %s.", log['stream'].strip())
        
        log.info(f"image built successfully: {image.tags}")
    except docker.errors.BuildError as e:
        log.error(f"build for {image_name} failed: {e}.")

    auth_config = {
        "username": "oauth2accesstoken",
        "password": get_gcp_access_token(service_account_creds),
    }

    # Push the image to Google Container Registry
    log.info(f"Pushing image to GCR: {image_name}")
    try:
        push_logs = docker_client.images.push(image_name, auth_config=auth_config, stream=True, decode=True)
        # for push_out in push_logs:
        #     if 'status' in push_out:
        #         log.debug(f"push-image {log['status']} {log.get('progress', '')}")
        log.info(f"image {image_name} pushed successfully")
    except docker.errors.APIError as e:
        log.error(f"push-image for {image_name}: failed to push image: {e}")

def gcp_build_image(build_context: PathLike, image_name: str, service_account_creds: dict):
    # TODO: complete this function
    pass