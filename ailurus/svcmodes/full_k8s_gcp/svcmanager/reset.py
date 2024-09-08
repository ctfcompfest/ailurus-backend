from ailurus.models import db
from datetime import datetime, timezone

from ..models import ManageServicePendingList
from ..types import ServiceManagerTaskType
from ..k8s import get_kubernetes_apiclient

import kubernetes
import logging

log = logging.getLogger(__name__)

def do_reset(body: ServiceManagerTaskType, **kwargs):
    team_id = body["team_id"]
    challenge_slug = body["challenge_slug"]
    
    deployment_name = "{}-t{}".format(challenge_slug, team_id)
    
    k8s_api_baseclient = get_kubernetes_apiclient()
    k8s_appsapi = kubernetes.client.AppsV1Api(k8s_api_baseclient)
    
    spec_patch = {
        "spec": {
            "template": {
                "metadata": {
                    "annotations": {
                        "kubectl.kubernetes.io/lastResetAt": datetime.now(timezone.utc).isoformat(),
                        "kubectl.kubernetes.io/doReset": "true",
                    }
                }
            }
        }
    }

    try:
        k8s_appsapi.patch_namespaced_deployment(
            name=deployment_name,
            namespace="default",
            body=spec_patch
        )
    except kubernetes.client.ApiException as e:
            log.error("restart-service: %s %s.", e.reason, e.body)