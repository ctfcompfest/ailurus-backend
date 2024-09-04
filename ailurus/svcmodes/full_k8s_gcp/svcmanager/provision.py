from ailurus.models import db, Service
from ailurus.utils.config import get_app_config
from typing import List, Mapping, Any, Tuple
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from ..k8s import get_kubernetes_apiclient
from ..schema import ServiceManagerTaskSchema, ServiceDetailSchema
from ..utils import get_gcp_configuration

import hashlib
import ipaddress
import json
import kubernetes
import logging
import os
import secrets
import yaml

log = logging.getLogger(__name__)

def generate_ssh_key() -> Tuple[str, str]:
    private_key = ed25519.Ed25519PrivateKey.generate()
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.NoEncryption()
    )

    public_key = private_key.public_key()
    public_key_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH
    )
    return private_pem.decode(), public_key_bytes.decode()

def get_mountpath_code(path: str) -> str:
    return hashlib.md5(path.encode()).hexdigest()

def calc_public_ports(challenge_id: int, ssh_port: int = None, expose_ports: List[int] = []) -> Mapping[int, int]:
    START_ALLOWED_PORT = 20000
    RANGE_PER_CHALL = 200

    min_port = challenge_id * RANGE_PER_CHALL + START_ALLOWED_PORT

    public_ports = {}
    if ssh_port:
        public_ports[ssh_port] = min_port + ssh_port % 50
    for i in range(len(expose_ports)):
        port = expose_ports[i] 
        public_ports[port] = min_port + (51 + i)
    return public_ports

def calculate_team_instanceip(cidr_block, team_id):
    padding = 30
    return str(ipaddress.ip_address(cidr_block.split("/")[0]) + team_id + padding)

def create_global_persistentvolumeclaim(k8s_coreapi: kubernetes.client.CoreV1Api) -> str:
    pvc_name = "pvc-global"
    service_persistentvolume = {
        "apiVersion": "v1",
        "kind": "PersistentVolumeClaim",
        "metadata": {
            "name": pvc_name,
        },
        "spec": {
            "accessModes": ["ReadWriteMany"],
            "resources": {
                "requests": {
                    "storage": "1Ti",
                }
            },
            "storageClassName": "standard-rwx",
        },
    }

    try:
        k8s_coreapi.create_namespaced_persistent_volume_claim("default", service_persistentvolume)
    except kubernetes.client.ApiException as e:
        if e.status == 409:
            log.info("create-global-pvc: conflict: persistent volume claim already exists.")
        else:
            log.error("create-global-pvc: %s %s.", e.reason, e.body)
    return pvc_name

def create_service_deployment(
        k8s_appsapi: kubernetes.client.AppsV1Api,
        team_id: int,
        challenge_slug: str,
        challenge_service_spec: Mapping[str, Any],
        challenge_image_name: str,
        checker_image_name: str = "",
    ) -> str:
    deployment_name = "{}-t{}".format(challenge_slug, team_id)
    service_deployment = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": deployment_name,
            "labels": {
                "challenge": challenge_slug,
                "team": str(team_id),
            }
        },
        "spec": {
            "replicas": 1,
            "selector": {
                "matchLabels": {
                    "challenge": challenge_slug,
                    "team": str(team_id),
                }
            },
            "template": {
                "metadata": {
                    "labels": {
                        "challenge": challenge_slug,
                        "team": str(team_id),
                    },
                    "annotations": {
                        "kubectl.kubernetes.io/doReset": "true",
                    }
                },
                "spec": {
                    "restartPolicy": "Always",
                    "volumes": [
                        {
                            "name": "configmap",
                            "configMap": {
                                "name": "configmap-{}-t{}".format(challenge_slug, team_id),
                                "items": [
                                    {"key": "copydata_script", "path": "init_script.sh"},
                                    {"key": "service_secret", "path": ".service_secret"},
                                    {"key": "flag_data", "path": "flag.txt"},
                                    {"key": "authorized_keys", "path": "authorized_keys"},
                                ],
                            },
                        },
                        {
                            "name": "flag-data",
                            "configMap": {
                                "name": "configmap-{}-t{}".format(challenge_slug, team_id),
                                "items": [
                                    {"key": "flag_data", "path": "flag.txt"},
                                ],
                            },
                        },
                        {
                            "name": "volpvc",
                            "persistentVolumeClaim": {"claimName": "pvc-global"},
                        },
                    ],
                    "initContainers": [
                        {
                            "name": "copy-container",
                            "image": challenge_image_name,
                            "command": ['sh', '/configmap/init_script.sh'],
                            "volumeMounts": [
                                {"name": "volpvc", "mountPath": "/destvolume"},
                                {"name": "configmap", "mountPath": "/configmap"},
                            ],
                            "env": [
                                {"name": "APPCONTAINER_RESET", "valueFrom": {"fieldRef": {"fieldPath": "metadata.annotations['kubectl.kubernetes.io/doReset']"}}},
                                {"name": "POD_NAME", "value": deployment_name},
                            ],
                            "resources": {
                                "requests": {
                                    "memory": challenge_service_spec["resources"]["memory"],
                                    "cpu": challenge_service_spec["resources"]["cpu"],
                                },
                            },
                        },
                        {
                            "name": "agent-checker",
                            "restartPolicy": "Always",
                            "image": checker_image_name,
                            "env": [
                                {"name": "CHECKER_INTERVAL", "value": "20"},
                                {"name": "CHECKER_SECRET", "value": "secret"},
                                {"name": "REPORT_API_ENDPOINT", "value": "{}/api/v2/agentchecker".format(get_app_config("WEBAPP_URL"))},
                                {"name": "REPORT_CHALL_SLUG", "value": challenge_slug},
                                {"name": "REPORT_TEAM_ID", "value": str(team_id)},
                                {"name": "APP_CONTAINER_FILESYSTEM", "value": "/app-container"},
                            ],
                            "resources": {
                                "requests": {
                                    "memory": "64Mi",
                                    "cpu": "250m",
                                },
                            },
                            "volumeMounts": [
                                dict(mountPath="/app-container" + mnt_path, name="volpvc", subPath=deployment_name + "/" + get_mountpath_code(mnt_path))
                                for mnt_path in challenge_service_spec["persistent_paths"]
                            ] + [
                                {"mountPath": "/configmap/.service_secret", "name": "configmap", "subPath": ".service_secret"},
                                {"mountPath": "/configmap/flag", "name": "flag-data"},
                            ]
                        }
                    ],
                    "containers": [
                        {
                            "name": "app",
                            "image": challenge_image_name,
                            "env": challenge_service_spec.get("env", []),
                            "resources": {
                                "requests": {
                                    "memory": challenge_service_spec["resources"]["memory"],
                                    "cpu": challenge_service_spec["resources"]["cpu"],
                                },
                                "limits": {
                                    "memory": challenge_service_spec["resources"]["memory"],
                                    "cpu": challenge_service_spec["resources"]["cpu"],
                                },
                            },
                            "ports": [
                                {"name": "{}-ssh".format(challenge_slug), "containerPort": challenge_service_spec["ssh_port"]},
                            ] + [
                                dict(name="{}-{}".format(challenge_slug, i), containerPort=challenge_service_spec["expose_ports"][i]["port"])
                                for i in range(len(challenge_service_spec["expose_ports"]))
                            ],
                            "volumeMounts": [
                                dict(mountPath=mnt_path, name="volpvc", subPath=deployment_name + "/" + get_mountpath_code(mnt_path))
                                for mnt_path in challenge_service_spec["persistent_paths"]
                            ] + [
                                {"mountPath": "/.service_secret", "name": "configmap", "subPath": ".service_secret"},
                                {"mountPath": challenge_service_spec["flag_path"], "name": "flag-data"},
                                {"mountPath": "/root/.ssh", "name": "volpvc", "subPath": deployment_name+"/ssh", "readOnly": True},
                            ]
                        }
                    ]
                }
            }
        },
    }
    try:
        k8s_appsapi.create_namespaced_deployment("default", service_deployment)
    except kubernetes.client.ApiException as e:
        if e.status == 409:
            log.info("create-service-deployment: conflict: deployment already exists.")
        else:
            log.error("create-service-deployment: %s %s.", e.reason, e.body)
    return deployment_name

def create_service_loadbalancer(
        k8s_coreapi: kubernetes.client.CoreV1Api,
        team_id: int,
        challenge_id: int,
        challenge_slug: str,
        challenge_service_spec: Mapping[str, Any],
        team_private_ip: str,
    ) -> str:
    service_lb_name = "lb-t{}".format(team_id)
    is_lb_service_available = False
    service_lb_service = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": service_lb_name,
            "annotations": {
                "networking.gke.io/load-balancer-type": "Internal",
            },
        },
        "spec": {
            "type": "LoadBalancer",
            "loadBalancerIP": team_private_ip,
            "selector": {
                "team": str(team_id)
            },
            "ports": [],
        }
    }
    try:
        k8s_lb_config: kubernetes.client.V1Service = k8s_coreapi.read_namespaced_service(service_lb_name, "default")
        k8s_lb_config_ports: List[kubernetes.client.V1ServicePort] = k8s_lb_config.spec.ports

        is_lb_service_available = True

        for port_cfg in k8s_lb_config_ports:
            if port_cfg.name.find("port-{}".format(challenge_slug)) == -1:
                service_lb_service["spec"]["ports"].append(port_cfg.to_dict())
    except kubernetes.client.ApiException as e:
        if e.status == 404:
            log.info("create-service-loadbalancer.read: not found: create new service.")
        else:
            log.error("create-service-loadbalancer.read: %s %s.", e.reason, e.body)

    expose_ports = [d["port"] for d in challenge_service_spec["expose_ports"]]
    public_ports = calc_public_ports(challenge_id, challenge_service_spec["ssh_port"], expose_ports)
    service_lb_service["spec"]["ports"].append({
        "name": "port-{}-ssh".format(challenge_slug),
        "protocol": "TCP",
        "port": public_ports[challenge_service_spec["ssh_port"]],
        "targetPort": "{}-ssh".format(challenge_slug),
    })
    for i in range(len(challenge_service_spec["expose_ports"])):
        port_cfg = challenge_service_spec["expose_ports"][i]
        service_lb_service["spec"]["ports"].append({
            "name": "port-{}-{}".format(challenge_slug, i),
            "protocol": port_cfg["protocol"],
            "port": public_ports[port_cfg["port"]],
            "targetPort": "{}-{}".format(challenge_slug, i),
        })
    
    try:
        if not is_lb_service_available:
            k8s_coreapi.create_namespaced_service("default", service_lb_service)        
        else:
            k8s_coreapi.replace_namespaced_service(service_lb_name, "default", service_lb_service)
    except kubernetes.client.ApiException as e:
        log.error("create-service-loadbalancer.exec: %s %s.", e.reason, e.body)

    return service_lb_name

def do_provision(body: ServiceManagerTaskSchema, **kwargs):
    team_id = body["team_id"]
    challenge_slug = body["challenge_slug"]
    challenge_id = body["challenge_id"]
    challenge_artifact_checksum = body["artifact_checksum"]
    challenge_testcase_checksum = body["testcase_checksum"]
    challenge_artifact_path = kwargs["artifact_folder"]

    service_secret = secrets.token_hex(8)
    ssh_privkey, ssh_pubkey = generate_ssh_key()
    
    with open(os.path.join(challenge_artifact_path, 'spec.yml')) as spec_file:
        challenge_service_spec = yaml.safe_load(spec_file)
    
    gcp_config_json = get_gcp_configuration()
    creds_json =  gcp_config_json["credentials"]
    project_id = creds_json['project_id']
    project_zone = gcp_config_json["zone"]
    
    team_private_ip = calculate_team_instanceip(gcp_config_json["loadbalancer_cidr"], team_id)
    repo_name =  gcp_config_json["artifact_registry"]

    challenge_image_name = "{}-docker.pkg.dev/{}/{}/{}:{}".format(
        project_zone, project_id, repo_name, challenge_slug, challenge_artifact_checksum
    )
    agentchecker_image_name = "{}-docker.pkg.dev/{}/{}/{}-agent-checker:{}".format(
        project_zone, project_id, repo_name, challenge_slug, challenge_testcase_checksum
    )

    combine_persistent_paths = " ".join([
        "\"{},{}\"".format(path, get_mountpath_code(path))
        for path in challenge_service_spec["persistent_paths"]
    ])
    COPYDATA_SCRIPT = """${{APPCONTAINER_RESET}} == "true" && rm -rf /destvolume/${{POD_NAME}};
mkdir -p /destvolume/${{POD_NAME}};

for PATH_CFG in {combine_persistent_paths};
do
    IFS=','
    set -- ${{PATH_CFG}}
    SRC_PATH=$1
    DEST_PATH=$2
    if [ ! -d /destvolume/${{POD_NAME}}/${{DEST_PATH}} ] && [ ! -f /destvolume/${{POD_NAME}}/${{DEST_PATH}} ];
    then
      cp -a ${{SRC_PATH}} /destvolume/${{POD_NAME}}/${{DEST_PATH}};
    fi
done

if [ ! -d /destvolume/${{POD_NAME}}/ssh ];
then
  mkdir -p /destvolume/${{POD_NAME}}/ssh;
fi
cp /configmap/authorized_keys /destvolume/${{POD_NAME}}/ssh/authorized_keys;
chmod -R 600 /destvolume/${{POD_NAME}}/ssh;
""".format(combine_persistent_paths=combine_persistent_paths)

    service_configmap = {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {
            "name": "configmap-{}-t{}".format(challenge_slug, team_id)
        },
        "data": {
            "authorized_keys": ssh_pubkey,
            "service_secret": service_secret,
            "copydata_script": COPYDATA_SCRIPT,
            "flag_data": "flag{placeholder}",
        },
    }

    k8s_api_baseclient = get_kubernetes_apiclient()
    k8s_coreapi = kubernetes.client.CoreV1Api(k8s_api_baseclient)
    k8s_appsapi = kubernetes.client.AppsV1Api(k8s_api_baseclient)

    try:
        k8s_coreapi.create_namespaced_config_map("default", service_configmap)
    except kubernetes.client.ApiException as e:
        if e.status == 409:
            log.info("create-service-configmap: conflict: config map exists.")
        else:
            log.error("create-service-configmap: %s %s.", e.reason, e.body)

    create_global_persistentvolumeclaim(k8s_coreapi)
    create_service_deployment(k8s_appsapi, team_id, challenge_slug, challenge_service_spec, challenge_image_name, agentchecker_image_name) 
    create_service_loadbalancer(k8s_coreapi, team_id, challenge_id, challenge_slug, challenge_service_spec, team_private_ip)

    expose_ports = [d["port"] for d in challenge_service_spec["expose_ports"]]
    public_ports = calc_public_ports(challenge_id, challenge_service_spec["ssh_port"], expose_ports)
    service_detail: ServiceDetailSchema = {
        "credentials": {
            "Address": "{}:{}".format(team_private_ip, public_ports[challenge_service_spec["ssh_port"]]),
            "Username": "root",
            "Private Key": ssh_privkey,
        },
        "public_adresses": [
            "{}:{}".format(team_private_ip, pubp)
            for realp, pubp in public_ports.items() if realp != challenge_service_spec["ssh_port"]
        ]
    }

    service = Service(
        team_id=team_id,
        challenge_id=challenge_id,
        order=0,
        secret=service_secret,
        detail=json.dumps(service_detail)
    )
    db.session.add(service)
    db.session.commit()