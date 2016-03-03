# -*- coding: utf-8 -*-
import pytest

import flaskr
PG_URI = 'postgresql://dbuser:password@localhost/example_bustardr_test'
engine = flaskr.Engine(PG_URI)
flaskr.db_session.bind = engine
flaskr.db_session.connect()


@pytest.yield_fixture
def client(request):
    flaskr.db_session.close()
    client = flaskr.app.test_client()
    flaskr.MetaData.create_all(engine)
    yield client
    flaskr.db_session.close()
    flaskr.MetaData.drop_all(engine)


def login(client, username, password):
    return client.post('/login', data=dict(
        username=username,
        password=password
    ), follow_redirects=True)


def logout(client):
    return client.get('/logout', follow_redirects=True)


def test_empty_db(client):
    """Start with a blank database."""
    rv = client.get('/')
    assert b'No entries here so far' in rv.data


def test_login_logout(client):
    """Make sure login and logout works"""
    username = flaskr.USERNAME
    password = flaskr.PASSWORD
    rv = login(client, username, password)
    assert b'log out' in rv.data
    rv = logout(client)
    assert b'log in' in rv.data
    rv = login(client, username + 'x', password)
    assert b'Invalid username' in rv.data
    rv = login(client, username, password + 'x')
    assert b'Invalid password' in rv.data


def test_messages(client):
    """Test that messages work"""
    login(client, flaskr.USERNAME, flaskr.PASSWORD)
    rv = client.post('/add', data=dict(
        title='<Hello>',
        content='<strong>HTML</strong> allowed here'
    ), follow_redirects=True)
    assert b'No entries here so far' not in rv.data
    assert b'&lt;Hello&gt;' in rv.data
    assert b'<strong>HTML</strong> allowed here' in rv.data
