# -*- coding: utf-8 -*-
import pytest

from bustard.http import jsonify, Headers, redirect, response_status_string


class TestHeaders:

    def test_normal(self):
        headers = Headers({'User-Agent': 'firefox/34'})
        assert headers['User-Agent'] == 'firefox/34'
        assert headers['user-agent'] == headers['User-Agent']

        headers.add('name', 'value')
        headers.add('name', 'value2')
        assert headers['name'] == headers['Name'] == 'value2'
        assert headers.get_all('Name') == ['value', 'value2']

        headers.set('Name', 'v')
        assert headers.get_all('Name') == ['v']

        headers['a'] = 'b'
        assert headers['a'] == 'b'
        assert headers.get_all('a') == ['b']

    def test_value_list(self):
        headers = Headers()
        headers.add('name', ['value', 'v2'])
        assert headers.get_all('name') == ['value', 'v2']
        assert set(headers.to_list()) == {('Name', 'value'), ('Name', 'v2')}

        h2 = Headers.from_list(
            [('name', 'v1'), ('Name', 'v2'), ('key', 'value')]
        )
        assert set(h2.to_list()) == {
            ('Name', 'v1'), ('Name', 'v2'), ('Key', 'value')
        }

        headers['foo'] = ['v1', 'v2']
        assert headers['foo'] == 'v2'
        assert headers.get_all('Foo') == ['v1', 'v2']


@pytest.mark.parametrize('url, code', [
    ('http://a.com', None),
    ('/a/b/c', 301),
])
def test_redirect(url, code):
    kwargs = {'url': url}
    if code:
        kwargs['code'] = code
    response = redirect(**kwargs)
    assert response.status_code == (code or 302)
    assert response.headers['location'] == url


@pytest.mark.parametrize('obj', [
    {'a': 1, 'b': 2},
    {'a': 'b', 'headers': Headers({'a': 'b'})},
    {},
])
def test_jsonify(obj):
    response = jsonify(obj)
    assert response.json() is not None


@pytest.mark.parametrize('code, result', [
    (200, '200 OK'),
    (1234, '1234 UNKNOWN'),
])
def test_response_status_string(code, result):
    assert response_status_string(code) == result
