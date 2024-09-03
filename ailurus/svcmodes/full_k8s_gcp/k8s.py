from ailurus.utils.config import get_config
from google.auth.transport.requests import Request
from google.cloud import container_v1 as gcpapi_container
from google.oauth2 import service_account

import kubernetes

def get_kubernetes_apiclient() -> kubernetes.client.ApiClient:
    creds_json = get_config("GCP_SERVICE_ACCOUNTS_CREDS", {})
    gcp_creds = service_account.Credentials.from_service_account_info(
        info=creds_json,
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )

    project_id = creds_json['project_id']
    cluster_zone = get_config("GCP_ZONE", "us-central1")
    event_slug = get_config("GCP_RESOURCES_PREFIX", "ailurus")
    cluster_name = event_slug + "-gke-cluster"

    k8s_cluster_path = f"projects/{project_id}/locations/{cluster_zone}/clusters/{cluster_name}"
    k8s_cluster_endpoint = gcpapi_container.ClusterManagerClient(
            credentials=gcp_creds
        ).get_cluster(
            name=k8s_cluster_path
        ).endpoint

    gcp_creds.refresh(Request())

    k8s_configuration = kubernetes.client.Configuration()
    k8s_configuration.host = f"https://{k8s_cluster_endpoint}"
    k8s_configuration.api_key = {"authorization": "Bearer " + gcp_creds.token}
    k8s_configuration.verify_ssl = False
    return kubernetes.client.ApiClient(configuration=k8s_configuration)
