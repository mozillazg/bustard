# -*- coding: utf-8 -*-
import base64
import json

import pytest

from bustard.utils import (
    MultiDict, parse_query_string, parse_basic_auth_header,
    to_header_key, to_text, to_bytes, json_dumps_default,
    Authorization
)


def test_multidict():
    d = MultiDict({'a': 1, 'b': 'a'})
    assert d['a'] == 1
    assert d['b'] == 'a'

    d['a'] = 2
    assert d['a'] == 2
    assert d.getlist('a') == [2]
    d['a'] = [1, 2]
    assert d['a'] == 2
    assert d.getlist('a') == [1, 2]

    assert d.to_dict() == {'a': [1, 2], 'b': ['a']}


def test_json_dumps_default():
    d = MultiDict({'a': 1})
    assert json.dumps(d, default=json_dumps_default) == json.dumps({'a': [1]})

    d['b'] = [1, 2, 3]
    assert (
        json.dumps(d, default=json_dumps_default, sort_keys=True) ==
        json.dumps(d.to_dict(), sort_keys=True)
    )


@pytest.mark.parametrize('qs, expect', [
    ('a=b', {'a': ['b']}),
    ('a=b&a=c', {'a': ['b', 'c']}),
    ('a=b&d&a=c', {'a': ['b', 'c']}),
    ('a=b&d=abc&a=c', {'a': ['b', 'c'], 'd': ['abc']}),
])
def test_parse_query_string(qs, expect):
    assert parse_query_string(qs) == expect


@pytest.mark.parametrize('key, expect', [
    ('abc', 'Abc'),
    ('abc_name', 'Abc_name'),
    ('UserAgent', 'Useragent'),
    ('user-Agent', 'User-Agent'),
    ('x-rage', 'X-Rage'),
])
def test_to_header_key(key, expect):
    assert to_header_key(key) == expect


@pytest.mark.parametrize('st, expect', [
    (b'abc', 'abc'),
    ('你好'.encode('utf8'), '你好'),
])
def test_to_text(st, expect):
    assert to_text(st) == expect


@pytest.mark.parametrize('bt, expect', [
    ('abc', b'abc'),
    ('你好', '你好'.encode('utf8')),
])
def test_to_bytes(bt, expect):
    assert to_bytes(bt) == expect


@pytest.mark.parametrize('value, expect', [
    ('', None),
    ('basic user:passwd', None),
    ('Basic user:passwd', None),
    ('basic user:{}'.format(base64.b64encode(b'passwd').decode()), None),
    ('basic {}'.format(base64.b64encode(b'user:passwd').decode()),
     Authorization('basic', 'user', 'passwd')
     ),
    ('Basic {}'.format(base64.b64encode(b'user:passwd').decode()),
     Authorization('basic', 'user', 'passwd')
     ),
])
def test_parse_basic_auth_header(value, expect):
    assert parse_basic_auth_header(value) == expect
