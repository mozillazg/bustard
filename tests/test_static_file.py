# -*- coding: utf-8 -*-
import os

import pytest

from bustard.app import Bustard
from bustard.views import StaticFilesView

app = Bustard()
current_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.yield_fixture
def client():
    yield app.test_client()


app.add_url_rule('/<path>',
                 StaticFilesView.as_view(static_dir=current_dir))


@pytest.mark.parametrize('filename', [
    'test_static_file.py',
    'test.png',
])
def test_ok(client, filename):
    response = client.get('/{}'.format(filename))
    with open(os.path.join(current_dir, filename), 'rb') as fp:
        assert response.content == fp.read()


@pytest.mark.parametrize('filename', [
    '../test_static_file.py',
    '../../test.png',
    'bustard-httpbin',
    'bustard-httpbin/abc',
])
def test_404(client, filename):
    response = client.get('/{}'.format(filename))
    assert response.status_code == 404
