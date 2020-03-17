import yaml
import boto3
import os
import sqlalchemy as sqla
from sqlalchemy.exc import OperationalError
import traceback

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


def set_secrets(credential_path, params_to_fetch, xnat, credential_source='file'):

    try:
        if credential_source == 'file':
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

        for var in 'XNAT_USER', 'XNAT_PASSWORD':
            os.environ[var] = os.environ[xnat.upper() + '_' + var]

        return 'TRUSTED', credentials, 'no error'

    except Exception as e:
        tb = traceback.format_exc()
        return 'LOCAL', e, tb


def assemble_db_uri(protocol='mysql+pymysql', db_name='brain_db', vars=['MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_HOST']):
    db_user, db_password, db_uri = [os.environ[var] for var in vars]
    return '{}://{}:{}@{}/{}'.format(protocol, db_user, db_password, db_uri, db_name)

def check_database(uri):
    db = sqla.create_engine(uri)
    try:
        db.connect()
        return True, 'no error'
    except (OperationalError, RuntimeError, OSError) as e:
        # todo: add check for specific runtime error
        # "cryptography is required for sha256_password or caching_sha2_password"
        tb = traceback.format_exc()
        return False, tb

def set_config_from_yaml(config_path, config_name):
    with open(config_path) as file:
        configs = yaml.safe_load(file)
        if configs and config_name in configs:
            config = configs[config_name]
            for var in config:
                os.environ[var] = str(config[var])
            return config

        else:
            print("WARNING: {} is not a block in {}. This is likely not a problem for the config override file."
                  .format(config_name, config_path))


def configure_database(config, kwargs):

    if 'mysql' in kwargs and kwargs['mysql'] in ['local', 'docker']:

        try:
            os.environ['MYSQL_HOST'] = config['MYSQL_' + kwargs['mysql'].upper() + '_HOST']
        except KeyError:
            print("WARNING: You selected a MySQL database but did not correctly configure your host. Make sure you "
                  "have MYSQL_LOCAL_HOST and/or MYSQL_DOCKER_HOST set in `config.yml`. Defaulting to the dockerized "
                  "host, but if you do not have a dockerized instance of the MBAM database running, SQLite will be "
                  "automatically used.")
            os.environ['MYSQL_HOST'] = 'mysql'

        database_exists, tb = check_database(assemble_db_uri())

        if not database_exists:
            print("WARNING: No MySQL instance found. This exception was handled by switching to an SQLite database and "
                  "is not fatal.  You can suppress this message in the future by running start_mbam.py with the "
                  "--database sqlite` option.  ")

            os.environ['SQLALCHEMY_DATABASE_URI'] = config['SQLITE_URI']

    else:
        os.environ['SQLALCHEMY_DATABASE_URI'] = config['SQLITE_URI']

def configure_xnat(xnat):
    try:
        for var in 'XNAT_HOST', 'DICOM_TO_NIFTI_COMMAND', 'FREESURFER_RECON_COMMAND', 'XNAT_PROJECT':
            os.environ[var] = os.environ[xnat + '_' + var]
    except KeyError as e:
        print("You've selected {} as your XNAT instance but {} is not configured.".format(xnat, var))


def set_config(config_path, override_config_path, config_name, xnat, **kwargs):

    config = set_config_from_yaml(config_path, config_name)
    override_config = set_config_from_yaml(override_config_path, config_name)

    if override_config:
        if 'xnat' in override_config:
            xnat = override_config['xnat']
        config.update(override_config)

    configure_database(config, kwargs)
    configure_xnat(xnat)


def set_env_vars(config_dir='.', secrets=True, config=True, env='trusted', xnat='mind',
                 params_to_fetch=parameters_to_fetch, **kwargs):

    if env in ['trusted', 'docker']:
        if secrets:

            config_type, result, tb = set_secrets(os.path.join(config_dir, 'credentials', 'secrets.yml'),
                                              params_to_fetch, xnat)

            if isinstance(result, Exception):
                print("Received exception when fetching credentials from the parameter store.  This isn't a problem if "
                  "you're not intending to use MBAM credentials.  If you are running `npm start_mbam` and would like to "
                  "suppress this message in the future, use `npm run start_mbam-local`.  The exception received was \n"
                  "{}".format(tb))

                xnat = env = 'local'


    if config:
        set_config(os.path.join(config_dir, 'config.yml'), os.path.join(config_dir, 'config.override.yml'), env.upper(),
                   xnat.upper(), **kwargs)