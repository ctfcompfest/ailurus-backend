from ailurus.models import db, Challenge, Service, Team, ProvisionMachine
from ailurus.utils.config import get_app_config
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.backends import default_backend
from typing import List, Dict, Mapping

from .schema import ServiceManagerTask

import base64
import boto3
import datetime
import flask
import ipaddress
import json
import logging
import os
import pika
import secrets
import yaml
import zipfile

log = logging.getLogger(__name__)

team_local_user = "ubuntu"
checker_local_user = "ctf"

def generator_public_services_info(team: Team, challenge: Challenge, services: List[Service]) -> Dict | List | str:
    """
    Service detail format:
    {
        "publish": {
            "IP": "1.2.3.4",
            "Username": "ubuntu",
            "Private Key": "<Key>",
        },
        "checker": {...}
    }
    """
    if len(services) == 0:
        return ""
    return json.loads(services[0].detail).get("publish", {}).get("IP", "")

def handler_svcmanager_request(**kwargs) -> flask.Response:
    ALLOWED_ACTION = ["get_credentials", "provision", "reset", "delete"]

    is_admin = kwargs.get('is_admin', False)
    if not kwargs.get('is_allow_manage', False) and not is_admin:
        return flask.jsonify(status="failed", message="failed."), 403
    request: flask.Request = kwargs.get('request')
    chall_id = kwargs.get('challenge_id')
    team_id = kwargs.get('team_id')
    
    cmd = request.args.get("action")
    if cmd not in ALLOWED_ACTION:
        return flask.jsonify(status="failed", message="command not implemented."), 400
    
    if cmd == "get_credentials":
        service = Service.query.filter_by(challenge_id=chall_id, team_id=team_id).first()
        if not service:
            return flask.jsonify(status="failed", message="invalid command."), 400
        return flask.jsonify(status="success", data=json.loads(service.detail).get("publish", {}))

    rabbitmq_conn = pika.BlockingConnection(
        pika.URLParameters(get_app_config("RABBITMQ_URI"))
    )
    rabbitmq_channel = rabbitmq_conn.channel()
    queue_name = get_app_config("QUEUE_SVCMANAGER_TASK", "svcmanager_task")
    rabbitmq_channel.queue_declare(queue_name, durable=True)

    artifact_path = os.path.join(get_app_config("DATA_DIR"), "challenges", f"artifact-{chall_id}.zip")
    with open(artifact_path, "rb") as fp:
        artifact_data = base64.b64encode(fp.read())

    taskbody = {
        "action": cmd,
        "initiator": ("team" if not is_admin else "admin"),
        "artifact": artifact_data.decode(),
        "challenge_id": chall_id,
        "team_id": team_id,
        "time_created": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    rabbitmq_channel.basic_publish(
        exchange='',
        routing_key=queue_name,
        body=base64.b64encode(
            json.dumps(
                taskbody
            ).encode()
        )
    )
    rabbitmq_conn.close()
    
    return flask.jsonify(status="success", message="success.")

def handler_svcmanager_task(body: ServiceManagerTask, **kwargs):
    if body["action"] == "provision" and body["initiator"] == "admin":
        return do_provision(body, **kwargs)
    elif body["action"] in "delete" and body["initiator"] == "admin":
        return do_delete(body, **kwargs)
    elif body["action"] == "reset":
        return do_reset(body, **kwargs)

def init_artifact(body, **kwargs):
    chall_id = body["challenge_id"]
    artifactroot_folder = os.path.join(get_app_config("DATA_DIR"), "..", "worker_data", "artifacts")
    artifact_folder = os.path.join(artifactroot_folder, f"artifact-{chall_id}")
    artifact_zipfile = os.path.join(artifactroot_folder, f"artifact-{chall_id}.zip")
    
    os.makedirs(artifactroot_folder, exist_ok=True)
    with open(artifact_zipfile, 'wb') as fp:
        fp.write(base64.b64decode(body["artifact"]))
    with zipfile.ZipFile(artifact_zipfile, "r") as fp:
        fp.extractall(artifact_folder)
    return artifact_folder

def generate_ssh_key():
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

def create_or_update_cloudformation_stack(credentials: Mapping[str, str], stack_name: str, template_body: str, params: Mapping[str, str]):
    log.info(f"start create or update cloudformation stack for '{stack_name}'.")

    try:
        aws_client = boto3.Session(**credentials).client('cloudformation')
        aws_client.describe_stacks(StackName=stack_name)
        is_stack_exists = True
    except aws_client.exceptions.ClientError as e:
        is_stack_exists = False
    
    try:
        try:
            template_params = json.loads(template_body)["Parameters"].keys()
        except:
            template_params = yaml.safe_load(template_body)["Parameters"].keys()
        
        reformat_params = [{'ParameterKey': x, 'ParameterValue': params[x]} for x in params.keys() if x in template_params]

        if is_stack_exists:
            log.debug('stack exists, updating stack.')
            aws_client.update_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Capabilities=['CAPABILITY_AUTO_EXPAND', 'CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
                Parameters=reformat_params,
            )
            
            log.debug('Waiting until stack %s updated.' % stack_name)
            aws_client.get_waiter('stack_update_complete').wait(StackName=stack_name)
            
            stack_info = aws_client.describe_stacks(StackName=stack_name)
            if stack_info['Stacks'][0]['StackStatus'] == 'UPDATE_COMPLETE':
                log.info(f'Stack {stack_name} updated successfully!')
                return stack_info['Stacks'][0]['Outputs']
            else:
                log.error(f'Stack update failed. Status: {stack_info["Stacks"][0]["StackStatus"]}')
        else:
            log.debug('Stack not exists, creating stack.')
            aws_client.create_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Capabilities=['CAPABILITY_AUTO_EXPAND', 'CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
                Parameters=reformat_params,
            )

            log.debug('Waiting until stack %s deployed.' % stack_name)
            aws_client.get_waiter('stack_create_complete').wait(StackName=stack_name)
            
            stack_info = aws_client.describe_stacks(StackName=stack_name)
            if stack_info['Stacks'][0]['StackStatus'] == 'CREATE_COMPLETE':
                log.info(f'Stack {stack_name} created successfully!')
                return stack_info['Stacks'][0]['Outputs']
            else:
                log.error(f'Stack creation failed. Status: {stack_info["Stacks"][0]["StackStatus"]}')
    except Exception as e:
        log.error(f'Stack create or update throw exception: {str(e)}')
    finally:
        log.info(f"create or update cloudformation finished.")
        aws_client.close()

def delete_cloudformation_stack(credentials: Mapping[str, str], stack_name: str):
    log.info(f"delete '{stack_name}' cloudformation stack.")
    try:
        aws_client = boto3.Session(**credentials).client('cloudformation')
        aws_client.delete_stack(StackName=stack_name)
    except aws_client.exceptions.ClientError as e:
        aws_client.close()
        log.error(f"error deleting cloudformation stack: {str(e)}")
        return

    try:
        log.debug('waiting until stack %s deleted.' % stack_name)

        aws_client.get_waiter('stack_delete_complete').wait(StackName=stack_name)
        stack_info = aws_client.describe_stacks(StackName=stack_name)
        if stack_info['Stacks'][0]['StackStatus'] == 'DELETE_COMPLETE':
            log.info(f'Stack {stack_name} deleted successfully!')
        else:
            log.error(f'Stack deletion failed. Status: {stack_info["Stacks"][0]["StackStatus"]}')
    except aws_client.exceptions.ClientError as e:
        if 'does not exist' in str(e):
            log.info(f'Stack {stack_name} deleted successfully!')
        else:
            log.error(f'Stack deletion failed raised an exception: {str(e)}')
    aws_client.close()

def create_or_get_provision_machine(challenge_id, artifact_folder):
    provision_machine = ProvisionMachine.query.filter_by(name=f"cloudformation-{challenge_id}").first()
    if provision_machine:
        return provision_machine
    
    with open(os.path.join(artifact_folder, "config.yml")) as fp:
        configs = yaml.safe_load(fp)
        
    stack_name = "{}-network-{}".format(configs["parameters"]["EventSlug"], challenge_id)
    with open(os.path.join(artifact_folder, configs["templates"]["network"])) as fp:
        template_body = fp.read()
    
    params = {
        **configs["parameters"],
        "ChallengeId": str(challenge_id),
    }
    stack_output = create_or_update_cloudformation_stack(
        configs["credentials"],
        stack_name,
        template_body,
        params,
    )
    if not stack_output:
        return None
    checker_privkey, checker_pubkey = generate_ssh_key()
    details = {
        "CheckerPublicKey": checker_pubkey,
        "CheckerPrivateKey": checker_privkey,
    }
    for output in stack_output:
        details[output['OutputKey']] = output['OutputValue']

    provision_machine = ProvisionMachine(name=f"cloudformation-{challenge_id}", host="aws_sdk", port=0, detail=json.dumps(details))
    db.session.add(provision_machine)
    db.session.commit()
    return provision_machine

def calculate_ip(cidr_block, team_id):
    padding = 30
    return str(ipaddress.ip_address(cidr_block.split("/")[0]) + team_id + padding)

def do_provision(body: ServiceManagerTask, **kwargs):
    artifact_folder = init_artifact(body, **kwargs)    
    provision_machine = create_or_get_provision_machine(body["challenge_id"], artifact_folder)
    if not provision_machine:
        return log.error("Failed to provision service for team={} challenge={}".format(body["team_id"], body["challenge_id"]))

    provision_machine_detail = json.loads(provision_machine.detail)

    with open(os.path.join(artifact_folder, "config.yml")) as fp:
        configs = yaml.safe_load(fp)
    machine_privkey, machine_pubkey = generate_ssh_key()
    stack_params = {
        **configs["parameters"],
        "MachinePrivateIpAddress": calculate_ip(configs["parameters"]["PrivateCidrBlock"], body["team_id"]),
        "MachinePublicKey": machine_pubkey,
        "TeamId": str(body["team_id"]),
        "ChallengeId": str(body["challenge_id"]),
        "MachineSecurityGroupId": provision_machine_detail["MachineSecurityGroupId"],
        "MachineSubnetId": provision_machine_detail["MachineSubnetId"],
    }
    stack_name = "{}-machine-{}-{}".fomrat(configs["parameters"]["EventSlug"], body["challenge_id"], body["team_id"])
    with open(os.path.join(artifact_folder, configs["templates"]["machine"])) as fp:
        template_body = fp.read()
        template_body = template_body.replace("{{Ailurus.CheckerPublicKey}}", provision_machine_detail["CheckerPublicKey"])

    stack_output = create_or_update_cloudformation_stack(configs['credentials'], stack_name, template_body, stack_params)
    if not stack_output:
        log.error("Failed to provision service for team={} challenge={}".format(body["team_id"], body["challenge_id"]))
        return False

    stack_output_dict = {}
    for output in stack_output:
        stack_output_dict[output['OutputKey']] = output['OutputValue']

    service_details = {
        "stack_name": stack_name,
        "publish": {
            "IP": stack_output_dict["MachinePrivateIp"],
            "Username": team_local_user,
            "Private Key": machine_privkey,
        },
        "checker": {
            "ip": stack_output_dict["MachinePrivateIp"],
            "username": checker_local_user,
            "private_key": provision_machine_detail["CheckerPrivateKey"],
            "instance_id": stack_output_dict["MachineInstanceId"],
        }
    }
    service = Service(
        team_id=body["team_id"],
        challenge_id=body["challenge_id"],
        detail=json.dumps(service_details),
        order=1,
        time_created=datetime.datetime.now(datetime.timezone.utc),
        secret=secrets.token_hex(8),
    )
    db.session.add(service)
    db.session.commit()

    log.info("provision service for team={} challenge={} completed.".format(body["team_id"], body["challenge_id"]))
    return True

def do_delete(body: ServiceManagerTask, **kwargs):
    artifact_folder = init_artifact(body, **kwargs)
    service: Service = Service.query.filter_by(challenge_id=body["challenge_id"], team_id=body["team_id"]).first()
    if not service:
        return log.error("service for team={} challenge={} not found, cannot execute delete action".format(body["team_id"], body["challenge_id"]))

    stack_name = json.loads(service.detail)["stack_name"]
    db.session.delete(service)
    db.session.commit()

    with open(os.path.join(artifact_folder, "config.yml")) as fp:
        configs = yaml.safe_load(fp)
    return delete_cloudformation_stack(configs["credentials"], stack_name)


def do_reset(body: ServiceManagerTask, **kwargs):
    service: Service = Service.query.filter_by(challenge_id=body["challenge_id"], team_id=body["team_id"]).first()
    if not service:
        return log.error("service for team={} challenge={} not found, cannot execute reset action".format(body["team_id"], body["challenge_id"]))

    artifact_folder = init_artifact(body, **kwargs)
    stack_name = json.loads(service.detail)["stack_name"]
    
    with open(os.path.join(artifact_folder, "config.yml")) as fp:
        configs = yaml.safe_load(fp)
    
    try:
        aws_client = boto3.Session(**configs["credentials"]).client('cloudformation')
        stack_spec = aws_client.describe_stacks(StackName=stack_name)
    except aws_client.exceptions.ClientError as e:
        aws_client.close()
        log.error(f"error fetching data for cloudformation stack: {str(e)}")
        return
    
    stack_parameters = stack_spec['Stacks'][0]['Parameters']
    raw_parameters = {x['ParameterKey']: x['ParameterValue'] for x in stack_parameters}

    stack_template = aws_client.get_template(StackName=stack_name)['TemplateBody']
    stack_template_str = json.dumps(stack_template)

    log.info('Rollback instance for %s' % stack_name)
    aws_client.close()

    delete_cloudformation_stack(configs["credentials"], stack_name)
    return  create_or_update_cloudformation_stack(configs['credentials'], stack_name, stack_template_str, raw_parameters)