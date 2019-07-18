import pytest
from cookiecutter_mbam.config import config_by_name, config_name
from cookiecutter_mbam.base.tasks import *
import mock
from pytest_mock import mocker

users = []

class MockUser():
    def __init__(self, id):
        self.id = id
        users.append(self)

    @classmethod
    def get_by_id(cls, id):
        return [user for user in users if user.id == id][0]

    def update(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class TestBaseTasks:

    @pytest.fixture(autouse=True)
    def setup_base_tests(self):
        self.user = MockUser(1)
        self.user.bagel = 'sesame'



class TestSetterAndGetterFactories(TestBaseTasks):

    def test_setter_factory_returns_function_that_can_set_an_attribute(self):
        setter = setter_factory(MockUser)
        assert callable(setter)
        val = setter('mint chip', self.user.id, 'ice_cream')
        assert val == 'mint chip'
        assert self.user.ice_cream == 'mint chip'

    def test_getter_factory_returns_function_that_can_get_an_attribute(self):
        getter = getter_factory(MockUser)
        assert callable(getter)
        val = getter('bagel', self.user.id)
        assert val == 'sesame'

    def test_multi_setter_returns_function_that_can_set_many_attributes(self):
        multi_setter = multi_setter_factory(MockUser)
        vals = {'vegetable':'celery', 'fruit':'peach'}
        assert callable(multi_setter)
        rv = multi_setter(vals, self.user.id)
        assert rv == vals


class TestEmailFunctions:
    @mock.patch('cookiecutter_mbam.base.tasks.smtplib')
    def test_send_email(self, mock_smtp, mocker):
        server = mocker.MagicMock()
        server.startttls = mocker.MagicMock()
        server.login = mocker.MagicMock()
        server.send_message = mocker.MagicMock()
        mock_smtp.SMTP = mocker.MagicMock()
        mock_smtp.SMTP.return_value = server
        msg = {'subject': "Hi, Elmo!", 'body':"It's Grover!"}
        send_email(('Elmo', 'elmo@sesamestreet.org', msg))
        mock_smtp.SMTP.assert_called_once()
        import pdb; pdb.set_trace()
        server.login.assert_called_once()
        assert server.login.call_args[0] == 'Elmo'
        server.send_message.assert_called_once()
        assert server.send_message.call_args == 'Hi, Elmo!'



