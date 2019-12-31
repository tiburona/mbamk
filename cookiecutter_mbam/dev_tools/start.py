import os
import argparse
import subprocess
import threading
from colorama import init, Fore

init(autoreset=True)

from set_env import parameters_to_fetch, set_env_vars

def thread(func):
    def wrapper(*args, **kwargs):
        x = threading.Thread(target=func, args=args, kwargs=kwargs)
        x.start()
    return wrapper


def execute(cmd, label, color, npm=False):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    while True:
        line = proc.stdout.readline().rstrip().decode('utf-8')
        if not line:
            break
        if not npm:
            line = getattr(Fore, color) + '{}'.format(label) + Fore.RESET + ' ' + line

@thread
def start_celery(dir, npm=False):
    execute('cd {}; celery -A cookiecutter_mbam.run_celery:celery worker --pool=gevent --concurrency=500 --loglevel '
            'info'.format(dir), 'CELERY', 'GREEN', npm=npm)

@thread
def start_redis(npm=False):
    execute('redis-server', 'REDIS', 'BLUE', npm=npm)


@thread
def start_flask(dir, npm=False):
    execute('cd {}; flask run'.format(dir), 'FLASK', 'RED', npm=npm)


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
            ['--noconfig'],
            {
                'help': "Skip setting config",
                'action': 'store_true',
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
                'choices': ['local', 'trusted']

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

    if args.celery:
        start_celery(args.celery_dir, npm=args.npm)

    if args.redis:
        start_redis(npm=args.npm)

    if args.flask:
        start_flask(args.celery_dir, npm=args.npm)










