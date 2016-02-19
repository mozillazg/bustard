# -*- coding: utf-8 -*-
import json
import os

import pytest

from bustard.app import Bustard
from bustard.utils import to_bytes, to_text

app = Bustard()
current_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.yield_fixture
def client():
    yield app.test_client()


@app.route('/echo', methods=['POST'])
def echo(request):
    files = request.files
    data = {
        'hello': to_text(files['hello'].read()),
    }
    data.update(request.form)
    return json.dumps(data)


@app.route('/bin', methods=['POST'])
def echo_bin(request):
    files = request.files
    return files['file'].read()


def test_upload(client):
    content = to_bytes('你好吗')
    files = {
        'hello': {
            'file': to_text(content),
            'filename': 'hello.txt',
        }
    }
    data = {
        'abc': 'a',
        'a': 'b',
    }
    expect_data = {}
    expect_data.update(data)
    expect_data.update({k: f['file'] for k, f in files.items()})
    response = client.post('/echo', data=data, files=files)
    assert response.json() == expect_data


def test_upload_bin(client):
    content = b''
    with open(os.path.join(current_dir, 'test.png'), 'rb') as f:
        content = f.read()
        f.seek(0)
        files = {
            'file': {
                'file': f.read(),
                'name': f.name,
            }
        }
    response = client.post('/bin', files=files)
    assert response.content == content
