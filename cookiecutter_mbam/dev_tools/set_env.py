import yaml
import boto3
import os

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
            '/TRUSTED/S3_SECRET_KEY',
            '/TRUSTED/S3_BUCKET',
            '/TRUSTED/SECRET_KEY',
            '/TRUSTED/SECURITY_PASSWORD_SALT',
            '/TRUSTED/MAIL_USERNAME',
            '/TRUSTED/MAIL_PASSWORD',
            '/TRUSTED/SEMAPHORE_HASH_ID'
        ]


def set_secrets(credential_path, params_to_fetch):

    try:
        with open(credential_path) as file:
            credentials = yaml.safe_load(file)

        for key in credentials:
            for var in credentials[key]:
                if credentials[key][var]:
                    os.environ[var] = credentials[key][var]

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
            os.environ[var] = str(config[var])

def set_env_vars(dir='.', secrets=True, config=True, env='trusted', params_to_fetch=parameters_to_fetch):

    if env == 'trusted' and secrets:

        config_type, result = set_secrets(os.path.join(dir, 'credentials', 'secrets.yml'), params_to_fetch)

        if isinstance(result, Exception):
            print("Received Exception when fetching credentials from the parameter store.  This isn't a problem if "
                  "you're not intending to use MBAM credentials.  If you are running `npm start` and would like to "
                  "suppress this message in the future, use `npm run start-local`.  The exception received was "
                  "{}".format(result))

            env = 'local'

    if config:
        set_config(os.path.join(dir, 'config.yml'), env.upper())