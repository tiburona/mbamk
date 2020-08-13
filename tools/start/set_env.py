import yaml
import boto3
import os
import sqlalchemy as sqla
from sqlalchemy.exc import OperationalError
import traceback

env_params = {
    'trusted': [
        'MIND_XNAT_USER', 'MIND_XNAT_PASSWORD', 'BACKUP_XNAT_USER', 'SEMAPHORE_AUTH_TOKEN', 'CLOUDFRONT_URL', 
        'CLOUDFRONT_KEY_ID', 'CLOUDFRONT_SECRET_KEY', 'S3_KEY_ID', 'S3_SECRET_KEY', 'S3_BUCKET', 'SECRET_KEY', 
        'SECURITY_PASSWORD_SALT', 'MAIL_USERNAME', 'MAIL_PASSWORD', 'SEMAPHORE_HASH_ID'
    ],
    'docker': [
        'MIND_XNAT_USER', 'MIND_XNAT_PASSWORD', 'BACKUP_XNAT_USER', 'BACKUP_XNAT_PASSWORD', 'CLOUDFRONT_URL', 
        'CLOUDFRONT_KEY_ID', 'CLOUDFRONT_SECRET_KEY', 'S3_KEY_ID', 'S3_SECRET_KEY', 'SECRET_KEY', 'MAIL_USERNAME', 
        'MAIL_PASSWORD'
    ],
    'staging': [
        'MIND_XNAT_USER', 'MIND_XNAT_PASSWORD', 'BACKUP_XNAT_USER', 'BACKUP_XNAT_PASSWORD', 'BASIC_AUTH_USERNAME', 
        'BASIC_AUTH_PASSWORD', 'CLOUDFRONT_URL', 'CLOUDFRONT_KEY_ID', 'CLOUDFRONT_SECRET_KEY', 'S3_KEY_ID', 
        'S3_SECRET_KEY', 'SECRET_KEY', 'SECURITY_PASSWORD_SALT', 'MAIL_USERNAME', 'MAIL_PASSWORD', 'MYSQL_USERNAME', 
        'MYSQL_PASSWORD', 'AMAZON_SMTP_PASSWORD', 'AMAZON_SMTP_USERNAME'],
    'qa': [
        'MIND_XNAT_USER', 'MIND_XNAT_PASSWORD', 'BACKUP_XNAT_USER', 'BACKUP_XNAT_PASSWORD', 'BASIC_AUTH_USERNAME',
        'BASIC_AUTH_PASSWORD', 'CLOUDFRONT_URL', 'CLOUDFRONT_KEY_ID', 'CLOUDFRONT_SECRET_KEY', 'S3_KEY_ID',
        'S3_SECRET_KEY', 'SECRET_KEY', 'SECURITY_PASSWORD_SALT', 'MAIL_USERNAME', 'MAIL_PASSWORD', 'MYSQL_USERNAME',
        'MYSQL_PASSWORD', 'AMAZON_SMTP_PASSWORD', 'AMAZON_SMTP_USERNAME'
    ]
}


def credentials_to_fetch(config_name):
    """Get the list of credentials to fetch from the credential server"""
    prefix = "/{}/".format(config_name).upper()
    if config_name in env_params:
        return [prefix + param for param in env_params[config_name]]
    else:
        return []


def set_secrets(credential_path, creds_to_fetch, xnat):
    """Get credentials to the AWS parameter store, then fetch more credentials and save them in the environment."""

    try:
        if os.path.exists(credential_path):
            print("Local secrets file exists. Will load AWS Parameter Store credentials from the file.")
            with open(credential_path) as file:
                credentials = yaml.safe_load(file)
            for key in credentials:
                for var in credentials[key]:
                    if credentials[key][var]:
                        os.environ[var] = credentials[key][var]
        else:
            print("Can not locate a local secrets file. Will attempt to load AWS Parameter Store credentials"
                  " directly from the environment.")
            credentials = {'empty:', 'dict'}

        aws_auth = {'aws_access_key_id': os.environ['PARAMETER_STORE_KEY_ID'],
                    'aws_secret_access_key': os.environ['PARAMETER_STORE_SECRET_KEY']}

        try:
            region_name = os.environ['AWS_DEFAULT_REGION']
        except KeyError:
            region_name = 'us-east-1'

        ssm_client = boto3.client('ssm', region_name=region_name, **aws_auth)

        for parameter_name in creds_to_fetch:
            # todo: this would speed up substantially if I used get_parameters.
            # it's just annoying because you can only get ten.
            response = ssm_client.get_parameter(
                Name=parameter_name,
                WithDecryption=True
            )

            parameter = response['Parameter']
            slash_index = parameter['Name'][1:].find('/') + 2
            os.environ[parameter['Name'][slash_index:]] = parameter['Value']

        for var in 'XNAT_USER', 'XNAT_PASSWORD':
            os.environ[var] = os.environ[xnat.upper() + '_' + var]

        return 'NONLOCAL', credentials, 'no error'

    except Exception as e:
        tb = traceback.format_exc()
        return 'LOCAL', e, tb


def assemble_db_uri(
        protocol='mysql+pymysql', db_name='brain_db', db_vars=('MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_HOST')
):
    """Build a complete database URI"""
    db_user, db_password, db_uri = [os.environ[var] for var in db_vars]
    return '{}://{}:{}@{}/{}'.format(protocol, db_user, db_password, db_uri, db_name)


def check_database(uri):
    """Look for an operational database"""
    db = sqla.create_engine(uri)
    try:
        db.connect()
        return True, 'no error'
    except (OperationalError, RuntimeError, OSError):
        # todo: add check for specific runtime error
        # "cryptography is required for sha256_password or caching_sha2_password"
        tb = traceback.format_exc()
        return False, tb


def set_config_from_yaml(config_path, config_name):
    """Load configuration from a YAML file and set environment variables"""
    try:
        with open(config_path) as file:
            configs = yaml.safe_load(file)
            if configs and config_name in configs:
                config = configs[config_name]
                for var in config:
                    os.environ[var] = str(config[var])
                return config

            else:
                print("INFO: {} is not a block in {}. This is likely not a problem for the config override file."
                      .format(config_name, config_path))

    except FileNotFoundError:
        print("INFO: No config override file exists.")


def configure_database(config, kwargs):
    """Set database configuration.

    First checks if we're on AWS, if so does nothing.  Otherwise looks for configuration that would give the host of
    either a local or dockerized MySQL instance, and defaults to Docker if that configuration is absent.  Checks to see
    if the specified (or default) MySQL database exists, and if it doesn't defaults to SQLite.
    """

    if kwargs['env'] in ['STAGING', 'QA', 'ALPHA', 'BETA']:
        print("It looks like we are in an AWS environment, so we will not configure MYSQL"
              " for local or mysql host.")
        return

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
    """Set XNAT configuration

    The config file has the XNAT variables with their specific XNAT instance prefix ('MIND', 'BACKUP', etc.) This sets
    the unprefixed environment variables.
    """
    for v in ['XNAT_HOST', 'DICOM_TO_NIFTI_COMMAND', 'FREESURFER_RECON_COMMAND', 'FS_TO_MESH_COMMAND', 'XNAT_PROJECT']:
        try:
            os.environ[v] = os.environ[xnat + '_' + v]
        except KeyError:
            print("You've selected {} as your XNAT instance but {} is not configured.".format(xnat, v))


def set_config(config_path, override_config_path, config_name, xnat, **kwargs):
    """Set configuration by calling function to read YAML files and set env variables. The database and XNAT both need
    more extensive logic for their config than just setting environment variables, so there are two dedicated methods
    for them."""

    config = set_config_from_yaml(config_path, config_name)
    override_config = set_config_from_yaml(override_config_path, config_name)

    if override_config:
        if 'XNAT' in override_config:
            xnat = override_config['XNAT']
        config.update(override_config)

    configure_database(config, dict(kwargs, env=config_name))
    configure_xnat(xnat)


def set_env_vars(config_dir='.', secrets=True, config=True, env='trusted', xnat='mind', **kwargs):
    """Call methods to set the environment with credentials and non-sensitive configuration"""

    if env not in ['local', 'test']:
        if secrets:
            config_type, result, tb = set_secrets(os.path.join(config_dir, 'credentials', 'secrets.yml'),
                                                  credentials_to_fetch(env), xnat)

            if isinstance(result, Exception):
                print("Received exception when fetching credentials from the parameter store.  This isn't a problem if "
                      "you're not intending to use MBAM credentials.  If you are running `npm start_mbam` and would "
                      "like to suppress this message in the future, use `npm run start_mbam-local`.  The exception "
                      "received was \n{}".format(tb))

                xnat = env = 'local'

    if config:
        set_config(os.path.join(config_dir, 'config.yml'), os.path.join(config_dir, 'config.override.yml'), env.upper(),
                   xnat.upper(), **kwargs)
