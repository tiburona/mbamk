import yaml
import boto3
import os
import argparse

parameters_to_fetch = [

            '/TRUSTED/MIND_XNAT_USER',
            '/TRUSTED/MIND_XNAT_PASSWORD',
            '/TRUSTED/BACKUP_XNAT_USER',
            '/TRUSTED/BACKUP_XNAT_PASSWORD',
            '/TRUSTED/SEMAPHORE_AUTH_TOKEN',
            '/TRUSTED/CLOUDFRONT_URL',
            '/TRUSTED/CLOUDFRONT_KEY_ID',
            '/TRUSTED/CLOUDFRONT_SECRET_KEY',
            '/TRUSTED/S3_KEY_ID',
            '/TRUSTED/S3_ACCESS_KEY',
            '/TRUSTED/SECRET_KEY',
            '/TRUSTED/SECURITY_PASSWORD_SALT',
            '/TRUSTED/MAIL_USERNAME',
            '/TRUSTED/MAIL_PASSWORD'
        ]


def set_secrets(credential_path, params_to_fetch):
    try:
        with open(credential_path) as file:
            credentials = yaml.safe_load(file)

        for key in credentials:
            for var in credentials[key]:
                os.environ[var] == credentials[key][var]

        aws_auth = {'aws_access_key_id': os.environ['PARAMETER_STORE_KEY_ID'],
                    'aws_secret_access_key': os.environ['PARAMETER_STORE_SECRET_KEY']}

        ssm_client = boto3.client('ssm', **aws_auth)

        for parameter_name in params_to_fetch:
            # todo: this would speed up substantially if I used get_parameters.
            # it's just annoying because you can only get ten.
            response = ssm_client.get_parameter(
                Name=parameter_name,
                WithDecryption=True
            )

            parameter = response['Parameter']

        os.environ[parameter['Name'][9:]] = parameter['Value']

        return 'TRUSTED', credentials

    except Exception as E:
        return 'LOCAL', E


def set_config(config_path, config_name):
    with open(config_path) as file:
        configs = yaml.safe_load(file)
        config = configs[config_name]
        for var in config:
            os.environ[var] = config[var]


def set_env_vars(credential_path=None, config_path=None, env='trusted', params_to_fetch=parameters_to_fetch):

    if env == 'trusted' and credential_path:
        config_type, result = set_secrets(credential_path, params_to_fetch)

        if type(result) == Exception:
            print("Received Exception when fetching credentials from the parameter store.  This isn't a problem if "
                  "you're not intending to use MBAM credentials.  If you are running `npm start` and would like to "
                  "suppress this message in the future, use `npm run start-local`.  The exception received was "
                  "{}".format(result))

            env = 'local'

    if config_path:
        set_config(config_path, env)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Set development environment variables.')

    args_to_add = [
        (
            ['--credentials'],
            {
                'type': str,
                'help': "relative or absolute path to the yaml file that stores an id/key pair to the parameter store",
                'default': './credentials/secrets.yml'
            }
        ),
        (
            ['--config'],
            {
                'type': str,
                'help': "relative or absolute path to yaml file with config to set before Flask app is initialized",
                'default': './config.yml'
            }
        ),
        (
            ['--set'],
            {
                'default': 'F',
                'help': "Reset the environment variables even if they have been set? T/F",
                'choices': ['T', 'F']
            }
        ),
        (
            ['--env'],
            {
                'default': 'local',
                'help': "The type of environment. Determines whether to attempt to retrieve credentials from the "
                        "parameter store.",
                'choices': ['local', 'trusted']

            }
        )
    ]

    for args, kwargs in argparse:
        parser.add_argument(*args, **kwargs)

    args = parser.parse_args()

    kwargs = {
        'credential_path': args.credential_path,
        'config_path': args.config_path,
        'env': args.env,
        'params_to_fetch': parameters_to_fetch
    }

    try:
        os.environ['FLASK_APP']
        if args.set == 'T':
            set_env_vars(**kwargs)

    except KeyError:
        set_env_vars(**kwargs)


