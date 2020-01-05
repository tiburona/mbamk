import os
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
        'label': ('FLASK', 'BLUE')
    }
}


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Set up the environment and start a development MBAM server.')

    args_to_add = [
        (
            ['--config_dir'],
        {
            'help': "Relative or absolute path to directory in which config files are stored",
            'default': '.'
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
                'help': "The type of environment. Determines whether to retrieve credentials from the parameter store.",
                'choices': ['local', 'trusted', 'docker', 'test']

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
        )
    ]

    for args, kwargs in args_to_add:
        parser.add_argument(*args, **kwargs)

    args = parser.parse_args()

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


    for arg in 'flask', 'redis', 'celery':

        if getattr(args, arg):
            # We only print color labels if we're running a local development server not through npm.
            if args.npm or args.env in ['test', 'docker']:
                output_labels = None
            else:
                output_labels = processes[arg]['labels']

            d = getattr(args, arg + '_dir') if hasattr(args, arg + '_dir') else '.'

            # The dockerized version of Flask has several commands that must be executed, not just `flask run`
            if args.env == 'docker' and arg == 'flask':
                for cmd in processes['flask']['docker-cmds']:
                    send_process(cmd, d, output_labels, docker=True)

            else:
                send_process(processes[arg]['cmd'], d, output_labels, docker=args.env == 'docker')


    if args.test:
        # stream_output is set to True here just to avoid calling shlex.split on a command with a semicolon in it
        # (see the execute function for more info)
        send_process('flask test', directory=args.flask_dir, docker=True, stream_output=True)













