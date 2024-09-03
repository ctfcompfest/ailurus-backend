from ailurus.models import Challenge

from .k8s import get_kubernetes_apiclient
from .schema import FlagrotatorTaskSchema

import kubernetes
import logging

log = logging.getLogger(__name__)

def handler_flagrotator_task(body: FlagrotatorTaskSchema, **kwargs):
    chall: Challenge = Challenge.query.filter_by(id=body["challenge_id"]).first()

    team_id = body["team_id"]
    challenge_slug = chall.slug
    flag_value = body["flag_value"]
    configmap_name = "configmap-{}-t{}".format(challenge_slug, team_id)
    
    k8s_api_baseclient = get_kubernetes_apiclient()
    k8s_coreapi = kubernetes.client.CoreV1Api(k8s_api_baseclient)

    try:
        k8s_cfgmap: kubernetes.client.V1ConfigMap = k8s_coreapi.read_namespaced_config_map(configmap_name, "default")
        k8s_cfgmap.data.update({"flag_data": flag_value})
        k8s_coreapi.patch_namespaced_config_map(configmap_name, "default", k8s_cfgmap)
    except kubernetes.client.ApiException as e:
        log.error("rotate-flag: team_id=%s chall_slug=%s - %s %s.", team_id, challenge_slug, e.reason, e.body)