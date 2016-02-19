# -*- coding: utf-8 -*-
import pytest

from bustard.app import Bustard
from bustard.utils import to_bytes

app = Bustard()


@pytest.yield_fixture
def client():
    yield app.test_client()


@app.route('/')
def get_session(request):
    value = request.session.get('name', '')
    return 'hello {}'.format(value)


@app.route('/set/<value>')
def set_session(request, value):
    request.session['name'] = value
    return ''


@app.route('/clear')
def clear_session(request):
    request.session.clear()
    return ''


def _get_session(client, value):
    response = client.get('/')
    assert response.content == to_bytes('hello {}'.format(value))


def test_set_session(client):
    client.get('/set/session')
    _get_session(client, 'session')


def test_clear_session(client):
    client.get('/set/hello')
    _get_session(client, 'hello')
    client.get('/clear')
    _get_session(client, '')
