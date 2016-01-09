#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import

import cgi
from collections import defaultdict
from http.cookies import SimpleCookie
import json

from .constants import HTTP_STATUS_CODES


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

    @property
    def url(self):
        netloc = self.environ['HTTP_HOST']
        return '{scheme}://{netloc}{path}'.format(
            scheme='http', netloc=netloc, path=self.path
        )

    @property
    def remote_addr(self):
        return self.environ.get('REMOTE_ADDR', '')

    def parse_form_data(self):
        if hasattr(self, '_form'):
            return

        fields = cgi.FieldStorage(fp=self.stream, environ=self.environ)
        _form = {}
        _files = {}
        if fields.length > 0:
            for key in fields:
                values = fields[key]
                if isinstance(values, list):
                    _form[key] = [x.value for x in values]
                elif getattr(values, 'filename', None) is not None:
                    _files[key] = values
                else:
                    _form[key] = [values.value]
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
        """Request cookies

        :rtype: dict
        """
        http_cookie = self.environ.get('HTTP_COOKIE', '')
        _cookies = {
            k: v.value
            for k, v in SimpleCookie(http_cookie)
        }
        return _cookies

    @property
    def headers(self):
        return {
            to_header_key(key.replace('HTTP_', '', 1).replace('_', '-')): value
            for key, value in self.environ.items()
            if key.startswith('HTTP_')
        }

    @property
    def data(self, as_text=False, encoding='utf-8'):
        if hasattr(self, '_content'):
            return self._content
        content = self.stream.read(int(self.content_length or 0))
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

    def __init__(self, content=b'', status_code=200, content_type='text/html',
                 headers=None):
        self._content = content
        self._status_code = status_code
        if headers is None:
            self._headers = {}
        else:
            self._headers = headers
        self._headers.setdefault('Content-Type', content_type)
        self._cookies = {}

    @property
    def data(self):
        return self._content

    @data.setter
    def data(self, value):
        self._content = value

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, value):
        self._content = value.encode('utf-8')

    @property
    def content_type(self, value):
        return self.headers.get('Content-Type', '')

    @content_type.setter
    def content_type(self, value):
        self.headers['Content-Type'] = value

    @property
    def status_code(self):
        return self._status_code

    @status_code.setter
    def status_code(self, value):
        self._status_code = value

    @property
    def status(self):
        code = self._status_code
        return response_status_string(code)

    @property
    def headers(self):
        return self._headers

    @property
    def content_type(self):
        return self._headers['Content-Type']

    @content_type.setter
    def content_type(self, value):
        self._headers['Content-Type'] = value

    @property
    def cookies(self):
        return self._cookies

    def set_cookie(self, key, value='', max_age=None, expires=None, path='/',
                   domain=None, secure=False, httponly=False):
        cookie = cookie_dump(
            key, value=value, max_age=max_age, expires=expires, path=path,
            domain=domain, secure=secure, httponly=httponly
        )
        self._cookies[key] = cookie

    def delete_cookie(self, key):
        self._cookies.pop(key, None)


def parse_query_string(query_string, encoding='utf-8'):
    query_dict = defaultdict(list)
    for query_item in query_string.split('&'):
        if '=' not in query_item:
            continue
        keyword, value = query_item.split('=', 1)
        query_dict[keyword].append(value.decode(encoding))
    return query_dict


def cookie_dump(key, value='', max_age=None, expires=None, path='/',
                domain=None, secure=False, httponly=False):
    """
    :rtype: ``Cookie.SimpleCookie``
    """
    cookie = SimpleCookie()
    cookie[key.encode('utf-8')] = value.encode('utf-8')
    for attr in ('max_age', 'expires', 'path', 'domain',
                 'secure', 'httponly'):
        attr_key = attr.replace('_', '-')
        attr_value = locals()[attr]
        if attr_value:
            cookie[key][attr_key] = attr_value
    return cookie


def response_status_string(code):
    """e.g. ``200 OK`` """
    mean = HTTP_STATUS_CODES.get(code, 'unknown').upper()
    return '{code} {mean}'.format(code=code, mean=mean)


def jsonify(obj=None, indent=2, sort_keys=True, **kwargs):
    if obj:
        kwargs = obj
    data = json.dumps(kwargs, indent=indent, sort_keys=sort_keys)
    response = Response(content_type='application/json')
    response.content = data
    return response


def redirect(*args, **kwargs):
    pass


def to_header_key(key):
    return '-'.join(x.capitalize() for x in key.split('-'))
