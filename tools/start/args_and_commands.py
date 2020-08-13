import argparse

# The processes dictionary stores the commands to run to start a process, as well as the colors those processes print to
# standard out in
processes = {
    'celery': {
        'cmd': 'celery -A cookiecutter_mbam.run_celery:celery worker --pool=gevent --concurrency=500 --loglevel info',
        'label': ('CELERY', 'GREEN')
    },
    'redis': {
        'cmd': 'redis-server',
        'label': ('REDIS', 'RED'),
    },
    'flask': {
        'cmd': {
            'local': ["flask run"],
            'trusted': ["flask run"],
            'docker': ["flask db upgrade", "gunicorn -w 2 --threads 4 -b :8000 --worker-class gthread "
                                           "'cookiecutter_mbam.app:create_app()'"],
            'staging': ["flask db upgrade", "gunicorn -w 2 --worker-tmp-dir /dev/shm --threads 4 -b :8000 "
                                            "--worker-class gthread 'cookiecutter_mbam.app:create_app()'"],
            'qa': ["flask db upgrade", "gunicorn -w 2 --threads 4 -b :8000 --worker-class gthread "
                                       "'cookiecutter_mbam.app:create_app()'"]
        },
        'label': ('FLASK', 'BLUE')
    }
}

deployments = {
    'staging': {
        'deploy': ['chmod +x ./build/cfn/build.sh', './build/cfn/build.sh']
    }
}

# This list defines the args that can be used with the 'run' command.
run_args = [
    (['--celery_dir'], {'help': "Relative or absolute path to directory in which Celery is initialized",
                        'default': '.'}),
    (['--flask_dir'], {'help': "Relative or absolute path to directory in which Flask is initialized",
                       'default': '.'}),
    (['-e', '--env'], {'default': 'trusted',
                       'help': "The type of environment. Determines configuration.",
                       'choices': ['local', 'docker', 'trusted', 'staging', 'qa']}),
    (['-f', '--flask'], {'action': 'store_true', 'help': "Start the Flask app"}),
    (['-c', '--celery'], {'action': 'store_true', 'help': "Start Celery worker"}),
    (['-r', '--redis'], {'action': 'store_true', 'help': "Start Redis"}),
    (['-n', '--npm'], {'action': 'store_true',
                       'help': 'script was executed by npm command'}),
    (['-x', '--xnat'], {'default': 'mind', 'choices': ['mind', 'backup', 'vvm'], 'help': 'XNAT instance'})
]

# This list defines the args that can be used with the 'test' command.
test_args = [
    (['-c', '--command'], {'dest': 'command', 'default': 'pytest ./tests --verbose', 'nargs': '?',
                           'const': 'pytest ./tests --verbose', 'help': "Pytest command to run"}),
    (['-d', '--docker'], {'const': 'cd build/docker; docker-compose build && docker-compose -f test.yml up',
                          'help': 'Docker command to run', 'dest': 'command', 'nargs': '?'})
]

# Right now the start package isn't being used for deployment.  Katie longs for the day it might be.
deploy_args = []


# Create an action for an argument such that the value is False if it begins with "no" and is otherwise True
class NegateAction(argparse.Action):

    def __call__(self, parser, ns, values, option_string=None):
        setattr(ns, self.dest, option_string[2:4] != 'no')


# These are arguments shared by all the commands
shared_args = [
    (['--config_dir'], {'help': "Relative or absolute path to directory in which config files are stored",
                        'default': './config'}),
    (['--config', '--noconfig'], {'help': "Set config", 'action': NegateAction, 'dest': 'config', 'nargs': '?',
                                  'default': True}),
    (['--secrets', '--nosecrets'], {'help': "Set secrets", 'action': NegateAction, 'dest': 'secrets', 'nargs': '?',
                                    'default': True}),
    (['--reset', '--no-reset'], {'help': "Reset env variables even if they have been set", 'action': NegateAction,
                                 'dest': 'reset', 'nargs': '?', 'default': False}),
]

# These are arguments shared by more than one environment that have different defaults in different environments.
shared_args_with_divergence = [
    (['-m', '--mysql'],
     {'choices': ['none', 'local', 'docker'], 'help': "Determines MySQL configuration. Note that a docker container "
                                                      "run on the developer's machine should use `docker`. If `none` "
                                                      "tests will use SQLite."},
     {'run': 'local', 'test': 'docker'}
     )
]


def parse_args():
    """Create the argument parser and parse the args"""

    # Initialize the argument parser
    parser = argparse.ArgumentParser(description='Run, test, or deploy MBAM.')

    # The creation of parent parser allows the run, test, and deploy subparsers to inherit shared arguments.
    parent_parser = argparse.ArgumentParser(add_help=False)

    # The shared_args tuple defines the arguments that the run, test, and deploy commands all get.
    for args, kwargs in shared_args:
        parent_parser.add_argument(*args, **kwargs)

    subparsers = parser.add_subparsers(help='commands')

    # Create the run, test, and deploy subparsers with the argument structure defined in the 'arg' tuples defined above
    for cmd, help_text, sub_args in [('run', 'Run an MBAM development server.', run_args),
                                     ('test', 'Test MBAM', test_args),
                                     ('deploy', 'Deploy MBAM', deploy_args)]:

        sparser = subparsers.add_parser(cmd, help=help_text, parents=[parent_parser],
                                        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        if 'cmd' == 'test':
            # '--docker' and '--command', the two unshared arguments to 'test', are mutually exclusive.
            sparser = sparser.add_mutually_exclusive_group()

        # Add the arguments to the subparsers
        for args, kwargs in sub_args:
            sparser.add_argument(*args, **kwargs)

    # subparsers.choices is where the list ['run', 'test', 'deploy'] gets stored
    for sparser in subparsers.choices:
        for args, kwargs, defaults in shared_args_with_divergence:
            # Add args that are shared between more than one env, but have different defaults depending on the env
            if sparser in defaults:
                subparsers.choices[sparser].add_argument(*args, **kwargs, default=defaults[sparser])

    return parser.parse_args()


def construct_kwargs(command, args):
    """Takes as input the arguments from the Argument Parser and returns the keyword arguments that will be sent to
    downstream functions in the start package."""
    kwargs = {}
    for key in ['config_dir', 'env', 'xnat', 'mysql', 'secrets', 'config']:
        if hasattr(args, key):
            kwargs[key] = getattr(args, key)
    if command == 'test':
        kwargs['env'] = 'test'
    return kwargs
