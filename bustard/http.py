# -*- coding: utf-8 -*-
import cgi
from http.cookies import SimpleCookie
import io
import json

from .constants import HTTP_STATUS_CODES
from .utils import (
    json_dumps_default, MultiDict, parse_query_string,
    to_header_key, to_text, to_bytes, parse_basic_auth_header
)


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
    def host(self):
        return self.environ['HTTP_HOST']

    @property
    def scheme(self):
        return self.environ['wsgi.url_scheme']

    @property
    def url(self):
        return '{scheme}://{host}{path}'.format(
            scheme=self.scheme, host=self.host, path=self.path
        )

    @property
    def remote_addr(self):
        return self.environ.get('REMOTE_ADDR', '')

    @property
    def form(self):
        if self.method not in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return {}
        content_type = self.content_type
        if (
            content_type.startswith('multipart/form-data; boundary=') or
            content_type.startswith('application/x-www-form-urlencoded')
        ):
            self.parse_form_data()
            return MultiDict(self._form)
        else:
            return {}

    def parse_form_data(self):
        if hasattr(self, '_form'):
            return

        fields = cgi.FieldStorage(fp=self.stream, environ=self.environ)
        _form = {}
        _files = {}
        if fields.length > 0 and fields.list:
            for key in fields:
                values = fields[key]
                if isinstance(values, list):
                    _form[key] = [x.value for x in values]
                elif 'Content-Type' in values.headers:
                    _files[key] = File(values.value, values.filename,
                                       values.type)
                else:
                    _form[key] = [values.value]
        self._form = _form
        self._files = _files

    @property
    def args(self):
        query_string = self.environ['QUERY_STRING']
        return MultiDict(parse_query_string(query_string))

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
            for (k, v) in SimpleCookie(http_cookie).items()
        }
        return _cookies

    @property
    def headers(self):
        _headers = {
            to_header_key(key.replace('HTTP_', '', 1).replace('_', '-')): value
            for key, value in self.environ.items()
            if key.startswith('HTTP_')
        }
        _headers.setdefault('Content-Type', self.content_type)
        _headers.setdefault('Content-Length', self.content_length)
        return Headers(_headers)

    @property
    def data(self, as_text=False, encoding='utf-8'):
        if hasattr(self, '_content'):
            return self._content

        if self.content_type in [
            'application/x-www-form-urlencoded',
            'multipart/form-data',
        ]:
            content = b''
        else:
            content = self.stream.read(int(self.content_length or 0))
        self._content = content
        if as_text:
            content = content.decode(encoding)
        return content

    @property
    def files(self):
        if self.method not in ['POST', 'PUT']:
            return {}
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

    @property
    def authorization(self):
        headers = self.headers
        auth_header_value = headers.get('Authorization', '')
        if len(auth_header_value.split()) > 1:
            return parse_basic_auth_header(auth_header_value)


class Response(object):

    def __init__(self, content=b'', status_code=200,
                 content_type='text/html; charset=utf-8',
                 headers=None):
        self._content = content
        self._status_code = status_code
        _headers = headers or {}
        _headers.setdefault('Content-Type', content_type)
        if isinstance(_headers, Headers):
            self._headers = _headers
        else:
            self._headers = Headers(_headers)
        self._cookies = SimpleCookie()
        self._load_cookies_from_headers()

    def _load_cookies_from_headers(self):
        cookies = self._headers.to_dict().pop('Set-Cookie', [])
        for cookie in cookies:
            self._cookies.load(cookie)

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, value):
        if isinstance(value, str):
            value = value.encode('utf-8')
        self._content = value
    body = data = content

    def get_data(self):
        return self._content

    @property
    def content_type(self, value):
        return self.headers.get('Content-Type', '')

    @content_type.setter
    def content_type(self, value):
        self.headers['Content-Type'] = value

    @property
    def content_length(self):
        return int(self.headers.get('Content-Length', '0'))

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

    @headers.setter
    def headers(self, value):
        self._headers = Headers(value)

    @property
    def content_type(self):
        return self._headers.get('Content-Type', '')

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
        self._cookies.load(cookie)

    def delete_cookie(self, key, max_age=0,
                      expires='Thu, 01-Jan-1970 00:00:00 GMT'):
        self.set_cookie(key, value='', max_age=max_age, expires=expires)

    @property
    def headers_list(self):
        # normal headers
        headers_list = list(self.headers.to_list())

        # set-cookies
        headers_list.extend(
            ('Set-Cookie', value.OutputString())
            for value in self.cookies.values()
        )
        return headers_list

    def json(self):
        return json.loads(to_text(self.data))

    def __repr__(self):
        return '<{} [{}]>'.format(self.__class__.__name__, self.status_code)


def cookie_dump(key, value='', max_age=None, expires=None, path='/',
                domain=None, secure=False, httponly=False):
    """
    :rtype: ``Cookie.SimpleCookie``
    """
    cookie = SimpleCookie()
    cookie[key] = value
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


def jsonify(*args, **kwargs):
    data = json.dumps(dict(*args, **kwargs), indent=2, sort_keys=True,
                      separators=(', ', ': '), default=json_dumps_default)
    data = data.encode('utf-8')
    response = Response(data + b'\n', content_type='application/json')
    response.headers['Content-Length'] = str(len(response.data))
    return response


def redirect(url, code=302):
    response = Response(status_code=code)
    response.headers['Location'] = url
    return response


class Headers(MultiDict):

    def add(self, key, value):
        key = to_text(to_header_key(key))
        if isinstance(value, (tuple, list)):
            self.data.setdefault(key, []).extend(map(to_text, value))
        else:
            self.data.setdefault(key, []).append(to_text(value))

    def set(self, key, value):
        self.__setitem__(key, value)

    def get_all(self, key):
        key = to_header_key(key)
        return self.data[key]

    @classmethod
    def from_list(cls, headers_list):
        headers = cls()
        for (k, v) in headers_list:
            headers.add(k, v)
        return headers

    def to_list(self):
        return [
            (k, v)
            for k, values in self.to_dict().items()
            for v in values
        ]

    def __getitem__(self, key):
        key = to_header_key(key)
        return super(Headers, self).__getitem__(key)

    def __setitem__(self, key, value):
        key = to_text(to_header_key(key))
        if isinstance(value, (list, tuple)):
            value = list(map(to_text, value))
        else:
            value = to_text(value)
        super(Headers, self).__setitem__(key, value)


class File:

    def __init__(self, data, filename,
                 content_type='application/octet-stream'):
        self.file = io.BytesIO(to_bytes(data))
        self.file.name = filename
        self.file.content_type = content_type

    def __getattr__(self, attr):
        return getattr(self.file, attr)
