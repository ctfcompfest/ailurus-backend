from typing import Mapping

import boto3
import json
import logging
import yaml
import traceback

log = logging.getLogger(__name__)
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
        except Exception as e:
            log.error("error parsing stack template as json: %s", str(e))
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
        log.error("{}", traceback.format_exc())
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

