import argparse

processes = {
    'celery': {
        'cmd': 'celery -A cookiecutter_mbam.run_celery:celery worker --pool=gevent --concurrency=500 --loglevel info',
        'label': ('CELERY', 'GREEN')
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
        'deploy': ['chmod +x ./build/cfn/build.sh', './build/cfn/build.sh']
    }
}

run_args = [
    (['--celery_dir'], {'help': "Relative or absolute path to directory in which Celery is initialized",
                        'default': '.'}),
    (['--flask_dir'], {'help': "Relative or absolute path to directory in which Flask is initialized",
                       'default': '.' }),
    (['-e', '--env'], {'default': 'trusted',
                       'help': "The type of environment. Determines configuration.",
                       'choices': ['local', 'trusted']}),
    (['-f', '--flask'], {'action': 'store_true', 'help': "Start the Flask app" }),
    (['-c', '--celery'], {'action': 'store_true', 'help': "Start Celery worker"}),
    (['-r', '--redis'], {'action': 'store_true', 'help': "Start Redis"}),
    (['-n', '--npm'], {'action': 'store_true',
                       'help': 'script was executed by npm command'}),
    (['-x', '--xnat'], {'default': 'mind', 'choices': ['mind', 'backup'], 'help': 'XNAT instance'})
]


test_args = [
    (['-c', '--command'], {'default': 'pytest ./tests --verbose', 'help': "Test command to run"})
]

deploy_args = []

shared_args = [
    (['--config_dir'], {'help': "Relative or absolute path to directory in which config files are stored",
                        'default': './config'}),
    (['--noconfig'], {'help': "Skip setting config", 'action': 'store_true'}),
    (['--nosecrets'], {'help': "Skip setting secrets", 'action': 'store_true'}),
    (['--reset'], {'help': "Reset the environment variables even if they have been set", 'action': 'store_true'}),
]

shared_args_with_divergence = [
    (['-m', '--mysql'],
     {'choices': ['none', 'local', 'docker'], 'help': "Determines MySQL configuration. Note that a docker container run "
                                                      "on the developer's machine should use `docker`. If `none` tests "
                                                      "will use SQLite."},
     {'run':'local', 'test': 'docker'}
     )
]

def parse_args():
    parser = argparse.ArgumentParser(description='Run, test, or deploy MBAM.')

    parent_parser = argparse.ArgumentParser(add_help=False)

    for args, kwargs in shared_args:
        parent_parser.add_argument(*args, **kwargs)

    subparsers = parser.add_subparsers(help='commands')

    for cmd, help_text, sub_args in [('run', 'Run an MBAM development server.', run_args),
                                     ('test', 'Test MBAM', test_args),
                                     ('deploy', 'Deploy MBAM', deploy_args)]:
        subparser = subparsers.add_parser(cmd, help=help_text, parents=[parent_parser])

        for args, kwargs in sub_args:
            subparser.add_argument(*args, **kwargs)

    for subparser in subparsers.choices:
        for args, kwargs, defaults in shared_args_with_divergence:
            if subparser in defaults:
                subparsers.choices[subparser].add_argument(*args, **kwargs, default=defaults[subparser])

    return parser.parse_args()


def construct_kwargs(command, args):
    kwargs = {}
    for key in ['config_dir', 'env', 'xnat', 'mysql']:
        if hasattr(args, key):
            kwargs[key] = getattr(args, key)
    for key in ['nosecrets', 'noconfig']:
        if hasattr(args, key):
            kwargs[key[2:]] = not getattr(args, key)
    if command == 'test':
        kwargs['env'] = 'test'
    if hasattr(args, 'env') and args.env == 'staging':
        kwargs['params_to_fetch'] = []
    return kwargs
