# Script that can start a process, run MBAM tests, or deploy a server, ensuring that those processes are initiated
# with the correct environment variables.

import os
import sys
import argparse
from set_env import set_env_vars, parameters_to_fetch
from execution import send_process


processes = {
    'celery': {
        'cmd': 'celery -A cookiecutter_mbam.run_celery:celery worker --pool=gevent --concurrency=500 --loglevel info',
        'labels': ('CELERY', 'GREEN')
    },
    'redis': {
        'cmd': 'redis-server',
        'label': ('REDIS', 'RED')
    },
    'flask': {
        'cmd': 'flask run',
        'docker_cmds': ['npm run build', 'flask db upgrade', 'flask run'],
        'staging_cmds': ['flask db upgrade', 'flask run'],
        'label': ('FLASK', 'BLUE')
    }
}

deployments = {
    'staging': {
        'deploy': ['chmod +x .build/cfn/build.sh', '.build/cfn/build.sh']
    }
}



if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Set up the environment and start a development MBAM server.')

    args_to_add = [
        (
            ['--config_dir'],
        {
            'help': "Relative or absolute path to directory in which config files are stored",
            'default': './config'
        }
        ),
        (
            ['--celery_dir'],
            {
                'help': "Relative or absolute path to directory in which Celery is initialized",
                'default': '.'
            }
        ),
        (
            ['--flask_dir'],
            {
                'help': "Relative or absolute path to directory in which Flask is initialized",
                'default': '.'
            }
        ),
        (
            ['--noconfig'],
            {
                'help': "Skip setting config",
                'action': 'store_true'
            }
        ),
        (
            ['--nosecrets'],
            {
                'help': "Skip setting secrets",
                'action': 'store_true'
            }
        ),
        (
            ['--reset'],
            {
                'help': "Reset the environment variables even if they have been set",
                'action': 'store_true'
            }
        ),
        (
            ['-e', '--env'],
            {
                'default': 'trusted',
                'help': "The type of environment. Determines configuration.",
                'choices': ['local', 'trusted', 'docker', 'test', 'staging']

            }
        ),
        (
            ['-f','--flask'],
            {
                'action': 'store_true',
                'help': "Start the Flask app"
            }
        ),
        (
            ['-c','--celery'],
            {
                'action': 'store_true',
                'help': "Start Celery worker",

            }
        ),
        (
            ['-r', '--redis'],
            {
                'action': 'store_true',
                'help': "Start Redis"

            }
        ),
        (
            ['-n', '--npm'],
            {
                'action': 'store_true',
                'help': 'script was executed by npm command'
            }
        ),
        (
            ['-x', '--xnat'],
            {
                'default': 'mind',
                'choices': ['mind', 'backup'],
                'help': 'XNAT instance'
            }
        ),
        (
            ['-t', '--test'],
            {
                'action': 'store_true',
                'help': 'Execute dockerized tests'
            }
        ),
        (
            ['-d', '--deploy'],
            {
                'choices': ['docker', 'staging'],
                'help': 'Deploy the app to the specified environment.'
            }
        )
    ]

    for args, kwargs in args_to_add:
        parser.add_argument(*args, **kwargs)

    args = parser.parse_args()

    if args.test and args.env != 'test':
        print("Warning: you are running tests but you haven't sent the environment to `test`.  If this is a mistake, "
              "include `--env test` as an argument to start.py.")

    kwargs = {
        'dir': args.config_dir,
        'env': args.env,
        'xnat': args.xnat,
        'config': not args.noconfig,
        'secrets': not args.nosecrets,
        'params_to_fetch': parameters_to_fetch,
    }

    try:
        os.environ['FLASK_APP']
        if args.reset:
            set_env_vars(**kwargs)

    except KeyError:
        set_env_vars(**kwargs)

    # Start a process or processes
    for arg in 'flask', 'redis', 'celery':

        if getattr(args, arg):
            # We only print color labels if we're running a local development server not through npm.
            if args.npm or args.env in ['test', 'docker', 'staging']:
                output_labels = None
                thread_wrap = False
            else:
                output_labels = processes[arg]['labels']
                thread_wrap = True

            d = getattr(args, arg + '_dir') if hasattr(args, arg + '_dir') else '.'

            # The dockerized version of Flask has several commands that must be executed, not just `flask run`
            if args.env in ['docker', 'staging'] and arg == 'flask':
                for cmd in processes['flask']['{}_cmds'.format(args.env)]:
                    send_process(cmd, d, output_labels, thread_wrap=thread_wrap)

            else:
                send_process(processes[arg]['cmd'], d, output_labels, thread_wrap=thread_wrap, stream_output=True)

    # Run tests
    if args.test:
        returncode = send_process('flask test', directory=args.flask_dir, thread_wrap=False)
        sys.exit(returncode)

    # Deploy a server
    if args.deploy:
        if args.deploy == 'staging':
            for cmd in deployments['staging']:
                send_process(cmd, '.', output_labels=None, thread_wrap=False)













