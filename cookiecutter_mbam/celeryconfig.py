broker_url = 'redis://localhost:6379'
result_backend = 'redis://localhost:6379'

task_serializer = 'pickle'
result_serializer = 'pickle'
accept_content = ['json', 'pickle']
enable_utc = True
