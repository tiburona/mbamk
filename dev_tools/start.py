import os
import argparse
import subprocess

from set_env import parameters_to_fetch, set_env_vars


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
            ['--reset'],
            {
                'default': 'F',
                'help': "Reset the environment variables even if they have been set?",
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
        ),
        (
            ['--start'],
            {
                'default': 'T',
                'help': "Start the app?",
                'choices': ['T', 'F']
            }
        )
    ]

    for args, kwargs in args_to_add:
        parser.add_argument(*args, **kwargs)

    args = parser.parse_args()

    kwargs = {
        'credential_path': args.credentials,
        'config_path': args.config,
        'env': args.env,
        'params_to_fetch': parameters_to_fetch
    }

    try:
        os.environ['FLASK_APP']
        if args.reset == 'T':
            set_env_vars(**kwargs)

    except KeyError:
        set_env_vars(**kwargs)


    if args.start == 'T':
        subprocess.run(['flask', 'run'])


