import pytest
import responses
import requests
from celery import Celery

celery = Celery(__name__)

@celery.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 5})
def task_to_test(self):
    s = requests.Session()
    r = s.get('http://10.1.1.17/data/experiments')
    if r.ok:
        return r.json()
    else:
        raise ValueError('oh no')

class TestParent:

    @responses.activate
    def success_response(self, mocked_uri, json, signature, method='GET', status=200):
        responses.add(getattr(responses, method), mocked_uri, status=status, json=json)
        return signature.apply()

    @responses.activate
    def failure_response(self, mocked_uri, signature, method='GET'):
        responses.add(getattr(responses, method), mocked_uri, status=403, json={'error': 'not found'})
        with pytest.raises(ValueError) as e_info:
            signature.apply(throw=True)

class TestChild(TestParent):

    def test_task_success(self):
        signature = task_to_test.s()
        task = self.success_response('http://10.1.1.17/data/experiments', {'title': 'laundry'}, signature)
        assert task.result['title'] == 'laundry'

    def test_task_failure(self):
        self.failure_response('http://10.1.1.17/data/experiments', signature = task_to_test.s())

#
# test = TestChild()
# test.test_task_success()
# test.test_task_failure()