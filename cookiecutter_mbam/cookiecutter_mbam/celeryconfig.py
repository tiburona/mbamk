broker_url = 'redis://localhost:6379'
result_backend = 'redis://localhost:6379'
# broker_url = 'redis://redis:6379'
# result_backend = 'redis://redis:6379'

task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
enable_utc = True

include = ['cookiecutter_mbam.xnat.tasks', 'cookiecutter_mbam.storage.tasks', 'cookiecutter_mbam.derivation.tasks',
           'cookiecutter_mbam.scan.tasks', 'cookiecutter_mbam.base.tasks']
