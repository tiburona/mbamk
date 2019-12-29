import subprocess
import shlex
import os

from environs import Env

env = Env()

def run_command(command_string):
    command = shlex.split(command_string)
    subprocess.run(command, shell=True, check=True)

os.environ['CFN_TEMPLATE_BUCKET'] = 's3://mbam-cfn-templates'
os.environ['CFN_PROFILE'] = 'mbam'

def sync_cloud_formation_templates():

    os.environ['AWS_ACCESS_KEY_ID'] = env['S3_KEY_ID']
    os.environ['AWS_SECRET_ACCESS_KEY'] = env['S3_SECRET_KEY']

    try:
        run_command("aws configure --profile mbam list")
    except subprocess.CalledProcessError:
        run_command("aws --region us-east-1 --profile mbam --output text")

    sync_command = "aws s3 sync {} {} --profile mbam".format(env('CFN_TEMPLATE_DIR'), env('CFN_TEMPLATE_BUCKET'))

    run_command(sync_command)

sync_cloud_formation_templates()