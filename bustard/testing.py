# -*- coding: utf-8 -*-
import collections
import mimetypes
import itertools
import io
import random
import sys
import time
import urllib

from .http import Headers, Response
from .utils import to_text, to_bytes


def run_wsgi_app(app, environ):

    response = []
    buffer = []

    def start_response(status, headers, exc_info=None):
        if exc_info is not None:
            raise (exc_info[0], exc_info[1], exc_info[2])
        response[:] = [status, headers]
        return buffer.append

    app_rv = app(environ, start_response)
    app_iter = itertools.chain(buffer, app_rv)

    return app_iter, response[0], Headers.from_list(response[1])


def build_multipart_body(data, files):
    body = io.BytesIO()
    values = collections.OrderedDict()
    values.update(data or {})
    values.update(files or {})

    def write(content):
        body.write(to_bytes(content))
    boundary = '{0}{1}'.format(time.time(), random.random())

    for name, value in values.items():
        write('--{}\r\n'.format(boundary))
        write('Content-Disposition: form-data; name="{}"'.format(name))

        if isinstance(value, dict):  # file field
            filename = value.get('name', '')
            if filename:
                write('; filename="{}"'.format(filename))
            write('\r\n')
            content_type = (
                value.get('content_type') or
                mimetypes.guess_type(filename)[0] or
                'application/octet-stream')
            write('Content-Type: {}\r\n'.format(content_type))
            if not content_type.startswith('text'):
                write('Content-Transfer-Encoding: binary')
            value = value['file']

        write('\r\n\r\n')
        write(value)
        write('\r\n')
    write('--{}--\r\n'.format(boundary))
    length = body.tell()
    body.seek(0)
    return body, length, boundary


class Client(object):

    def __init__(self, app, host='localhost', port='80', cookies=None):
        self.app = app
        self.host = host
        self.environ_builder = EnvironBuilder()
        self.cookies = cookies or {}

    def open(self, path, method, params=None, data=None,
             files=None, headers=None, cookies=None,
             content_type='', charset='utf-8', follow_redirects=False):
        if isinstance(headers, dict):
            headers = Headers(headers)
        content_type = content_type or (headers or {}).get('Content-Type', '')
        cookies = cookies or {}
        cookies.update(self.cookies)
        body = None
        if files:
            body_reader, _, boundary = build_multipart_body(data, files)
            body = body_reader.read()
            body_reader.close()
            data = None
            content_type = 'multipart/form-data; boundary={}'.format(boundary)

        environ = self.environ_builder.build_environ(
            path=path, method=method, params=params,
            data=data, body=body, headers=headers,
            cookies=cookies,
            content_type=content_type, charset=charset
        )
        app_iter, status, headers = run_wsgi_app(self.app, environ)
        status_code = int(status[:3])
        response = Response(b''.join(app_iter), status_code=status_code,
                            headers=headers,
                            content_type=content_type)
        self.cookies.update({
            k: v.value
            for (k, v) in response.cookies.items()
        })
        if status_code in (301, 302, 303, 307) and follow_redirects:
            new_path = headers['Location']
            return self.open(new_path, 'GET')
        return response

    # get = functools.partialmethod(open, method='GET', data=None)
    def get(self, path, params=None, **kwargs):
        return self.open(path, method='GET', params=params, **kwargs)

    def options(self, path, **kwargs):
        return self.open(path, method='OPTIONS', **kwargs)

    def head(self, path, **kwargs):
        return self.open(path, method='HEAD', **kwargs)

    def trace(self, path, **kwargs):
        return self.open(path, method='TRACE', **kwargs)

    def post(self, path, **kwargs):
        return self.open(path, method='POST', **kwargs)

    def put(self, path, **kwargs):
        return self.open(path, method='PUT', **kwargs)

    def patch(self, path, **kwargs):
        return self.open(path, method='PATCH', **kwargs)

    def delete(self, path, **kwargs):
        return self.open(path, method='DELETE', **kwargs)


class EnvironBuilder(object):

    def __init__(self, host='localhost', port='80',
                 multithread=False, multiprocess=False,
                 run_once=False, environ_base=None,
                 url_scheme='http'):
        self.host = host
        self.port = str(port)
        if self.port == '80':
            self.http_host = self.host
        else:
            self.http_host = '{}:{}'.format(self.host, self.port)
        self.default_environ = {
            'SERVER_NAME': self.host,
            'GATEWAY_INTERFACE': 'CGI/1.1',
            'SERVER_PORT': self.port,
            'REMOTE_HOST': '',
            'CONTENT_LENGTH': '',
            'SCRIPT_NAME': '',
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'REMOTE_ADDR': None,
            'REMOTE_PORT': None,

            'wsgi.version': (1, 0),
            'wsgi.url_scheme': url_scheme,
            'wsgi.errors': sys.stderr,
            'wsgi.multithread': multithread,
            'wsgi.multiprocess': multithread,
            'wsgi.run_once': run_once,
        }
        if environ_base:
            self.default_environ.update(environ_base)

    def build_environ(self, path='/', method='GET', params=None,
                      data=None, body=None, headers=None, cookies=None,
                      content_type='', charset='utf-8'):
        query_string = ''
        path = to_text(path)
        if '?' in path:
            path, query_string = path.split('?', 1)
        if isinstance(params, (dict, list, tuple)):
            query_string = query_string + '&' + urllib.parse.urlencode(params)

        if isinstance(data, dict):
            body = to_bytes(urllib.parse.urlencode(data), encoding=charset)
            content_type = 'application/x-www-form-urlencoded'
        elif data:
            body = to_bytes(data, encoding=charset)

        environ = self.default_environ.copy()
        environ.update({
            'REQUEST_METHOD': method,
            'PATH_INFO': path,
            'QUERY_STRING': query_string,
            'CONTENT_TYPE': content_type,
            'CONTENT_LENGTH': str(len(body or b'')),
            'wsgi.input': io.BytesIO(body),
        })
        # headers
        if headers is not None:
            for k, v in headers.to_dict().items():
                key = 'HTTP_' + k.replace('-', '_').upper()
                value = ', '.join(v)
                environ.update({key: value})
        environ.setdefault('HTTP_HOST', self.http_host)
        # cookies
        if cookies is not None:
            http_cookie = '; '.join('='.join([k, v])
                                    for (k, v) in cookies.items())
            environ.update({'HTTP_COOKIE': http_cookie})

        return environ
