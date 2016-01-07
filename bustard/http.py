#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import cgi
from collections import defaultdict
import json

from .const import HTTP_STATUS_CODES


class Request(object):

    def __init__(self, environ):
        self.environ = environ

    @property
    def method(self):
        """``GET``, ``POST`` etc."""
        return self.environ['REQUEST_METHOD']

    @property
    def path(self):
        return self.environ['PATH_INFO']

    def parse_form_data(self):
        if hasattr(self, '_form'):
            return

        fields = cgi.FieldStorage(fp=self.stream, environ=self.environ)
        _form = {}
        _files = {}
        for key in fields:
            value = fields[key]
            if isinstance(value, list):
                _form[key] = [x.value for x in value]
            elif getattr(value, 'filename', None) is not None:
                _files[key] = value
            else:
                _form[key] = [value.value]
        self._form = _form
        self._files = _files

    @property
    def form(self):
        self.parse_form_data()
        return self._form

    @property
    def args(self):
        query_string = self.environ['QUERY_STRING']
        return parse_query_string(query_string)

    @property
    def values(self):
        raise NotImplementedError

    @property
    def cookies(self):
        raise NotImplementedError

    @property
    def headers(self):
        return {
            key: value
            for key, value in self.environ.items()
            if key.startswith('HTTP_')
        }

    @property
    def data(self, as_text=False, encoding='utf-8'):
        if hasattr(self, '_content'):
            return self._content
        content = self.stream.read()
        self._content = content
        if as_text:
            content = content.decode(encoding)
        return content

    @property
    def files(self):
        self.parse_form_data()
        return self._files

    @property
    def stream(self):
        return self.environ['wsgi.input']

    def get_json(self, encoding='utf-8'):
        content = self.data.decode(encoding)
        try:
            return json.loads(content)
        except ValueError:
            return

    @property
    def content_type(self):
        return self.environ.get('CONTENT_TYPE', '')

    @property
    def content_length(self):
        return self.environ.get('CONTENT_LENGTH', '')

    @property
    def is_json(self):
        content_type = self.content_type
        if content_type.startswith('application/json') or (
                content_type.startswith('application/') and
                content_type.endswith('+json')
                ):
            return True
        return False

    @property
    def is_ajax(self):
        """The ``X-Requested-With`` header equal to ``HttpRequest`` """
        requested_with = self.headers.get('HTTP_X_REQUESTED_WITH', '').lower()
        return requested_with == 'xmlhttprequest'


class Response(object):

    def __init__(self, content='', status_code=200, content_type='text/html',
                 headers=None):
        self.content = content
        self.status_code = status_code
        if headers is None:
            self._headers = {}
        else:
            self._headers = headers
        self._headers['Content-Type'] = content_type

    @property
    def status(self):
        code = self.status_code
        try:
            mean = HTTP_STATUS_CODES[code].upper()
        except KeyError:
            mean = 'UNKNOWN'
        return '{code} {mean}'.format(code=code, mean=mean)

    @property
    def headers(self):
        return self._headers

    @property
    def content_type(self):
        return self._headers['Content-Type']

    @content_type.setter
    def content_type(self, value):
        self._headers['Content-Type'] = value

    def set_cookie(self, key, value='', max_age=None, expires=None, path='/',
                   domain=None, secure=None, httponly=False):
        cookie = cookie_dump(
            key, value=value, max_age=max_age, expires=expires, path=path,
            domain=domain, secure=secure, httponly=httponly
        )
        self._headers.setdefault('Set-Cookie', []).append(cookie)


def parse_query_string(query_string, encoding='utf-8'):
    query_dict = defaultdict(list)
    for query_item in query_string.split('&'):
        if '=' not in query_item:
            continue
        keyword, value = query_item.split('=', 1)
        query_dict[keyword].append(value.decode(encoding))
    return query_dict


def cookie_dump(key, value='', max_age=None, expires=None, path='/',
                domain=None, secure=None, httponly=False):
    raise NotImplementedError
