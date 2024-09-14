from ailurus.models import db, Service
from sqlalchemy import delete

from typing import List

from ..models import ManageServicePendingList
from ..k8s import get_kubernetes_apiclient
from ..types import ServiceManagerTaskType
from ..utils import get_gcp_configuration

import kubernetes
import logging

log = logging.getLogger(__name__)

def delete_service_deployment(k8s_appsapi: kubernetes.client.AppsV1Api, team_id: int, challenge_slug: str):
    deployment_name = "{}-t{}".format(challenge_slug, team_id)
    try:
        k8s_appsapi.delete_namespaced_deployment(deployment_name, "default")
    except kubernetes.client.ApiException as e:
        if e.status == 404:
            log.error("delete-service-deployment: not found: failed delete.")
        else:
            log.error("delete-service-deployment: %s %s.", e.reason, e.body)
        
def delete_service_loadbalancer(k8s_coreapi: kubernetes.client.CoreV1Api, team_id: int, challenge_slug: str):
    service_lb_name = "lb-t{}".format(team_id)
    service_lb_service = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": service_lb_name,
            "annotations": {
                "networking.gke.io/load-balancer-type": "Internal",
                "networking.gke.io/internal-load-balancer-allow-global-access": "true",
                "networking.gke.io/internal-load-balancer-subnet": get_gcp_configuration()["loadbalancer_subnet"],
            },
        },
        "spec": {
            "type": "LoadBalancer",
            "loadBalancerIP": "",
            "selector": {
                "team": str(team_id)
            },
            "ports": [],
        }
    }
    try:
        k8s_lb_config: kubernetes.client.V1Service = k8s_coreapi.read_namespaced_service(service_lb_name, "default")
        k8s_lb_config_ports: List[kubernetes.client.V1ServicePort] = k8s_lb_config.spec.ports

        service_lb_service["spec"]["loadBalancerIP"] = k8s_lb_config.spec.load_balancer_ip
        for port_cfg in k8s_lb_config_ports:
            if port_cfg.name.find("port-{}".format(challenge_slug)) == -1:
                exist_port = port_cfg.to_dict()
                del exist_port["nodePort"]
                service_lb_service["spec"]["ports"].append(exist_port)
    except kubernetes.client.ApiException as e:
        if e.status == 404:
            log.error("delete-service-loadbalancer: not found: failed to delete.")
            return
        else:
            log.error("delete-service-loadbalancer: failed read lb: %s %s.", e.reason, e.body)
    try:
        if len(service_lb_service["spec"]["ports"]) == 0:
            k8s_coreapi.delete_namespaced_service(service_lb_name, "default")        
        else:
            k8s_coreapi.replace_namespaced_service(service_lb_name, "default", service_lb_service)
    except kubernetes.client.ApiException as e:
        log.error("delete-service-loadbalancer: failed to delete: %s %s.", e.reason, e.body)
    return service_lb_name

def do_delete(body: ServiceManagerTaskType, **kwargs):
    team_id = body["team_id"]
    challenge_id = body["challenge_id"]
    challenge_slug = body["challenge_slug"]
    
    k8s_api_baseclient = get_kubernetes_apiclient()
    k8s_coreapi = kubernetes.client.CoreV1Api(k8s_api_baseclient)
    k8s_appsapi = kubernetes.client.AppsV1Api(k8s_api_baseclient)
    
    delete_service_deployment(k8s_appsapi, team_id, challenge_slug)
    delete_service_loadbalancer(k8s_coreapi, team_id, challenge_slug)
    try:
        k8s_coreapi.delete_namespaced_config_map("configmap-{}-t{}".format(challenge_slug, team_id), "default")
    except kubernetes.client.ApiException as e:
        if e.status == 404:
            log.error("delete-service-configmap: not found: failed to delete.")
        else:
            log.error("delete-service-configmap: %s %s.", e.reason, e.body)

    db.session.execute(
        delete(Service).where(
            Service.team_id == team_id,
            Service.challenge_id == challenge_id,
        )
    )
    db.session.commit()