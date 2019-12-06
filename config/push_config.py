import boto3
import yaml
import requests
import subprocess
import os
import sys
from set_dev_env_vars import set_env_vars
from environs import Env

env = Env()


sync_ps, sync_sem, sync_cfn = sys.argv[1:]

credentials = set_env_vars(credential_path='./credentials/secrets.yml', config_path='./config.yml')

if sync_ps or sync_sem:

    with open('./config.yml') as file:

        configs = yaml.safe_load(file)

        if sync_ps:

            aws_auth = {'aws_access_key_id': credentials['PARAMETER_STORE']['KEY_ID'],
                        'aws_secret_access_key': credentials['PARAMETER_STORE']['SECRET_KEY']}

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

        if sync_sem:

            sem_auth_token = env('SEMAPHORE_AUTH_TOKEN')
            sem_hash_id = env('SEMAPHORE_HASH_ID')

            head = {'Authorization': 'token {}'.format(sem_auth_token)}
            sem_url = 'https://api.semaphoreci.com/v2/'

            get_vars_url = sem_url + 'projects/{project_id}/env_vars'.format(sem_hash_id)

            current_vars = requests.get(get_vars_url, headers=head).json()

            for var in current_vars:
                id = var['id']
                data = {'name': var['name'], 'content': str(configs['Test'][var['name']])}
                requests.patch(url=sem_url + 'env_vars/{id}'.format(id), data=data)


if sync_cfn:

    os.environ['AWS_ACCESS_KEY_ID'] = env['S3_KEY_ID']
    os.environ['AWS_SECRET_ACCESS_KEY'] = env['S3_SECRET_KEY']

    status = subprocess.run(
        ['awscli', 'sync', env('CFN_TEMPLATE_DIR'), env('CFN_TEMPLATE_BUCKET'), '--profile', 'mbam']
    )