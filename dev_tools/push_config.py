import boto3
import yaml
import requests
import subprocess
import os
import argparse
import shlex
from environs import Env

env = Env.read_env()


def sync_parameter_store(configs):
    aws_auth = {'aws_access_key_id': os.environ['PARAMETER_STORE_KEY_ID'],
                'aws_secret_access_key': os.environ['PARAMETER_STORE_SECRET_KEY']}

    ssm_client = boto3.client('ssm', **aws_auth)

    for config in configs:
        if config != 'Test':
            for var in configs[config]:
                key = '/' + config + '/' + var
                val = str(configs[config][var])

                ssm_client.put_parameter(
                    Name=key,
                    Value=val,
                    Type='String',
                    Overwrite=True
                )


def sync_semaphore(configs):
    sem_auth_token = env('SEMAPHORE_AUTH_TOKEN')
    sem_hash_id = env('SEMAPHORE_HASH_ID')

    head = {'Authorization': 'token {}'.format(sem_auth_token)}
    sem_url = 'https://api.semaphoreci.com/v2/'

    get_vars_url = sem_url + 'projects/{}/env_vars'.format(sem_hash_id)

    current_vars = requests.get(get_vars_url, headers=head).json()

    for var in current_vars:
        id = var['id']
        data = {'name': var['name'], 'content': str(configs['Test'][var['name']])}
        requests.patch(url=sem_url + 'env_vars/{id}'.format(id), data=data)

def run_command(command_string):
    command = shlex.split(command_string)
    subprocess.run(command)


def sync_cloud_formation_templates():

    env = Env()
    env.read_env()

    os.environ['AWS_ACCESS_KEY_ID'] = env('S3_KEY_ID')
    os.environ['AWS_SECRET_ACCESS_KEY'] = env('S3_SECRET_KEY')

    try:
        run_command("aws configure --profile mbam list")
    except subprocess.CalledProcessError:
        run_command("aws configure set region us-east-1 --profile mbam")

    sync_command = "aws s3 sync {} {} --profile mbam".format(env('CFN_TEMPLATE_DIR'), env('CFN_TEMPLATE_BUCKET'))

    run_command(sync_command)


def push_config(sync_ps=False, sync_sem=False, sync_cfn=False):

    try:
        os.environ['PARAMETER_STORE_KEY_ID']
    except KeyError:
        with open ('./credentials/secrets.yml') as file:
            credentials = yaml.safe_load(file)
            os.environ['PARAMETER_STORE_KEY_ID'] = credentials['PARAMETER_STORE']['PARAMETER_STORE_KEY_ID']
            os.environ['PARAMETER_STORE_SECRET_KEY'] = credentials['PARAMETER_STORE']['PARAMETER_STORE_SECRET_KEY']

    if sync_ps or sync_sem:
        with open('./config.yml') as file:
            configs = yaml.safe_load(file)
            if sync_ps:
                sync_parameter_store(configs)
            if sync_sem:
                sync_semaphore(configs)

    if sync_cfn:
        sync_cloud_formation_templates()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Push configuration changes to the AWS parameter store, Semaphore, and"
                                                 " the s3 bucket that stores Cloud Formation templates.")

    arg_info = [
        ('ps', "Push configuration to the AWS parameter store."),
        ('sem', "Push configuration to Sempahore."),
        ('cfn', "Sync Cloud Formation Templates.")
    ]

    args_to_add = [
        (
            ['--{}'.format(argname)],
            {'default': 'F', 'help': helptext + " T/F", 'choices': ['T', 'F']}
        )
        for argname, helptext in arg_info
    ]

    for args, kwargs in args_to_add:
        parser.add_argument(*args, **kwargs)

    args = parser.parse_args()

    push_config(**{'sync_' + dest: getattr(args, dest) == 'T' for  dest in ['ps', 'sem', 'cfn']})


