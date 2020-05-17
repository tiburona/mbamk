import argparse

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
            'local': ['flask run'],
            'trusted': ['flask run'],
            'docker': ['flask db upgrade', "gunicorn -w 2 --threads 4 -b :8000 --worker-class gthread 'cookiecutter_mbam.app:create_app()'"],
            'staging': ['flask db upgrade', "gunicorn -w 2 --worker-tmp-dir /dev/shm --threads 4 -b :8000 --worker-class gthread 'cookiecutter_mbam.app:create_app()'"],
            'qa': ['flask db upgrade', "gunicorn -w 2 --worker-tmp-dir /dev/shm --threads 4 -b :8000 --worker-class gthread 'cookiecutter_mbam.app:create_app()'"]
        },
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
                       'choices': ['local','docker','trusted','staging','qa']}),
    (['-f', '--flask'], {'action': 'store_true', 'help': "Start the Flask app" }),
    (['-c', '--celery'], {'action': 'store_true', 'help': "Start Celery worker"}),
    (['-r', '--redis'], {'action': 'store_true', 'help': "Start Redis"}),
    (['-n', '--npm'], {'action': 'store_true',
                       'help': 'script was executed by npm command'}),
    (['-x', '--xnat'], {'default': 'mind', 'choices': ['mind', 'backup', 'vvm'], 'help': 'XNAT instance'})
]


test_args = [
    (['-c', '--command'], {'dest':'command', 'default': 'pytest ./tests --verbose', 'nargs': '?',
                           'const': 'pytest ./tests --verbose', 'help': "Pytest command to run"}),
    (['-d', '--docker'], {'const': 'cd build/docker; docker-compose build && docker-compose -f test.yml up',
                          'help':'Docker command to run', 'dest':'command', 'nargs':'?'})
]

deploy_args = []

class NegateAction(argparse.Action):
    def __call__(self, parser, ns, values, option):
        setattr(ns, self.dest, option[2:4] != 'no')

shared_args = [
    (['--config_dir'], {'help': "Relative or absolute path to directory in which config files are stored",
                        'default': './config'}),
    (['--config', '--noconfig'], {'help': "Set config", 'action': NegateAction, 'dest':'config', 'nargs':'?',
                                  'default': True}),
    (['--secrets', '--nosecrets'], {'help': "Set secrets", 'action': NegateAction, 'dest':'secrets', 'nargs':'?',
                                  'default': True}),
    (['--reset', '--no-reset'], {'help': "Reset env variables even if they have been set", 'action': NegateAction,
                                 'dest':'reset', 'nargs':'?', 'default': False}),
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
        sparser = subparsers.add_parser(cmd, help=help_text, parents=[parent_parser],
                                        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        if 'cmd' == 'test':
            sparser = sparser.add_mutually_exclusive_group()

        for args, kwargs in sub_args:
            sparser.add_argument(*args, **kwargs)

    for sparser in subparsers.choices:
        for args, kwargs, defaults in shared_args_with_divergence:
            if sparser in defaults:
                subparsers.choices[sparser].add_argument(*args, **kwargs, default=defaults[sparser])

    return parser.parse_args()


def construct_kwargs(command, args):
    kwargs = {}
    for key in ['config_dir', 'env', 'xnat', 'mysql', 'secrets', 'config']:
        if hasattr(args, key):
            kwargs[key] = getattr(args, key)
    if command == 'test':
        kwargs['env'] = 'test'
    # if hasattr(args, 'env') and args.env == 'staging':
    #     kwargs['params_to_fetch'] = []
    return kwargs
