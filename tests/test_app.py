# -*- coding: utf-8 -*-
import os

import pytest

from bustard.app import Bustard
from .utils import CURRENT_DIR

app = Bustard(template_dir=os.path.join(CURRENT_DIR, 'templates'))


@pytest.yield_fixture
def client():
    yield app.test_client()


@app.route('/hello/<name>')
def hello(request, name):
    return app.render_template('hello.html', name=name)


def test_hello(client):
    url = app.url_for('hello', name='Tom')
    response = client.get(url)
    assert response.data.strip() == b'hello Tom /hello/Tom'
