import pytest
from cookiecutter_mbam.config import config_by_name, config_name
from cookiecutter_mbam.base.tasks import *

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
        self.user.foo = 'bar'



class TestSetterAndGetterFactories(TestBaseTasks):

    def test_setter_factory_returns_function_that_can_set_an_attribute(self):
        setter = setter_factory(MockUser)
        assert callable(setter)
        val = setter('foo', self.user.id, 'bar')
        assert val == 'foo'
        assert self.user.bar == 'foo'

    def test_getter_factory_returns_function_that_can_get_an_attribute(self):
        getter = getter_factory(MockUser)
        assert callable(getter)
        val = getter('foo', self.user.id)
        assert val == 'foo'

    def test_multi_setter_returns_function_that_can_set_many_attributes(self):
        multi_setter = multi_setter_factory(MockUser)
        vals = {'vegetable':'celery', 'fruit':'peach'}
        assert callable(multi_setter)
        rv = multi_setter(vals, self.user.id)
        assert rv == vals






tsf = TestSetterAndGetterFactories()

tsf.test_setter_factory_returns_function_that_can_set_an_attribute()
tsf.test_getter_factory_returns_function_that_can_get_an_attribute()

