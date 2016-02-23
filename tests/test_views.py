# -*- coding: utf-8 -*-
import pytest

from bustard.app import Bustard
from bustard.views import View
from bustard.utils import to_bytes

app = Bustard()


@pytest.yield_fixture
def client():
    yield app.test_client()


def login_required(view):

    def wrapper(request, *args, **kwargs):
        if request.method == 'DELETE':
            app.abort(403)
        return view(request, *args, **kwargs)
    return wrapper


class IndexView(View):
    decorators = (login_required,)

    def get(self, request, name):
        return name

    def post(self, request, name):
        return '{} post'.format(name)

    def delete(self, request, name):
        return 'delete'


app.add_url_rule('/hello/(?P<name>\w+)', IndexView.as_view())


class TestView:

    def test_get(self, client):
        name = 'Tom'
        response = client.get(app.url_for('IndexView', name=name))
        assert response.data == to_bytes(name)

    def test_post(self, client):
        name = 'Tom'
        response = client.post(app.url_for('IndexView', name=name))
        assert response.data == to_bytes(name + ' post')

    def test_404(self, client):
        response = client.get('/hello/--')
        assert response.status_code == 404

    def test_405(self, client):
        response = client.put('/hello/aaa')
        assert response.status_code == 405

    def test_403(self, client):
        response = client.delete('/hello/aaa')
        assert response.status_code == 403
