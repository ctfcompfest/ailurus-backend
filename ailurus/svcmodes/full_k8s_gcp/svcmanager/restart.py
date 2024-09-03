from ailurus.models import db
from datetime import datetime, timezone

from ..models import ManageServicePendingList
from ..schema import ServiceManagerTaskSchema
from ..k8s import get_kubernetes_apiclient

import kubernetes
import logging

log = logging.getLogger(__name__)

def do_restart(body: ServiceManagerTaskSchema, **kwargs):
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
                        "kubectl.kubernetes.io/lastRestartAt": datetime.now(timezone.utc).isoformat(),
                        "kubectl.kubernetes.io/doReset": "false",
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

    pending_list = ManageServicePendingList.query.filter_by(
         team_id=team_id,
         challenge_slug=challenge_slug,
         is_done=False,
    )
    if pending_list:
        pending_list.is_done = True
        db.session.commit()