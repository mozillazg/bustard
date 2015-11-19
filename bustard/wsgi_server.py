#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import datetime
import socket
import StringIO
import sys
import time
import urllib


class WSGIServer(object):
    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    request_queue_size = 5
    allow_reuse_address = True
    default_request_version = 'HTTP/1.1'
    server_version = 'WSGIServer/0.1'
    weekdayname = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    monthname = [None,
                 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    def __init__(self, server_address):
        # 创建 socket
        self.socket = socket.socket(self.address_family, self.socket_type)
        # 绑定
        self.server_bind(server_address)
        # 监听
        self.server_activate()
        # 基本的 environ
        self.setup_environ()
        self.headers_set = []

    def server_bind(self, server_address):
        if self.allow_reuse_address:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.socket.bind(server_address)
        self.server_address = self.socket.getsockname()

        host, port = self.socket.getsockname()[:2]
        self.server_name = socket.getfqdn(host)
        self.server_port = port

    def server_activate(self):
        self.socket.listen(self.request_queue_size)

    def setup_environ(self):
        """https://www.python.org/dev/peps/pep-0333/#environ-variables"""
        # Set up base environment
        env = self.base_environ = {}
        env['SERVER_NAME'] = self.server_name
        env['GATEWAY_INTERFACE'] = 'CGI/1.1'
        env['SERVER_PORT'] = str(self.server_port)
        env['REMOTE_HOST'] = ''
        env['CONTENT_LENGTH'] = ''
        env['SCRIPT_NAME'] = ''

    def get_app(self):
        return self.application

    def set_app(self, application):
        self.application = application

    def serve_forever(self):
        while 1:
            self.handle_one_request()
            self.client_connection.close()

    def handle_one_request(self):
        self.client_connection, client_address = self.socket.accept()
        # self.raw_request = raw_request = self.client_connection.recv(65537)
        self.raw_request = raw_request = self.client_connection.recv(65536)

        self.parse_request(raw_request)
        self.parse_headers(raw_request)
        env = self.get_environ()

        print('[%s] "%s %s %s"' % (
            datetime.datetime.now(), env['REQUEST_METHOD'],
            env['PATH_INFO'], env['SERVER_PROTOCOL'],
        ))

        result = self.application(env, self.start_response)
        self.finish_response(result)

    def parse_request(self, raw_request):
        # GET /foo?a=1&b=2 HTTP/1.1
        first_line = raw_request.split('\r\n', 1)[0].strip()
        (self.request_method,   # GET
         self.path,             # /foo?a=1&b=2
         self.request_version   # HTTP/1.1
         ) = first_line.split()

    def parse_headers(self, raw_request):
        header_string = raw_request.split('\r\n\r\n', 1)[0]
        self.headers = headers = {}
        for header in header_string.splitlines()[1:-1]:
            k, v = header.split(':', 1)
            if headers.get(k):
                headers[k] += ',' + v.strip()  # 多个相同的 header
            else:
                headers[k] = v.strip()

    def get_environ(self):
        """https://www.python.org/dev/peps/pep-0333/#environ-variables"""
        env = self.base_environ.copy()
        env['REQUEST_METHOD'] = self.request_method

        if '?' in self.path:
            path, query = self.path.split('?', 1)
        else:
            path, query = self.path, ''
        env['PATH_INFO'] = urllib.unquote(path)
        env['QUERY_STRING'] = query

        env['CONTENT_TYPE'] = self.headers.get('Content-Type')
        env['CONTENT_LENGTH'] = self.headers.get('Content-Length')

        env['SERVER_PROTOCOL'] = self.request_version
        env['wsgi.version'] = (1, 0)
        env['wsgi.url_scheme'] = 'http'
        env['wsgi.input'] = StringIO.StringIO(self.raw_request)
        env['wsgi.errors'] = sys.stderr
        env['wsgi.multithread'] = False
        env['wsgi.multiprocess'] = True
        env['wsgi.run_once'] = False

        for k, v in self.headers.items():
            k = k.replace('-', '_').upper()
            if k in env:
                continue
            env['HTTP_' + k] = v
        return env

    def start_response(self, status, response_headers, exc_info=None):
        server_headers = [
            ('Date', self.date_time_string()),
            ('Server', self.version_string()),
        ]
        response_headers = list(response_headers) + server_headers

        if exc_info:
            try:
                if self.headers_set:
                    # Re-raise original exception if headers sent
                    raise exc_info[0], exc_info[1], exc_info[2]
            finally:
                exc_info = None     # avoid dangling circular ref

        self.headers_set[:] = [status, response_headers]

    def finish_response(self, body):
        try:
            status, headers = self.headers_set
            # status line
            response = self.default_request_version + ' ' + status + '\r\n'
            # headers
            response += '\r\n'.join([': '.join(x) for x in headers])
            response += '\r\n\r\n'
            # body
            for d in body:
                response += d
            self.client_connection.sendall(response)
        finally:
            self.client_connection.close()

    def version_string(self):
        return self.server_version

    def date_time_string(self, timestamp=None):
        if timestamp is None:
            timestamp = time.time()
        year, month, day, hh, mm, ss, wd, y, z = time.gmtime(timestamp)
        s = '%s, %02d %3s %4d %02d:%02d:%02d GMT' % (
            self.weekdayname[wd],
            day, self.monthname[month], year,
            hh, mm, ss
        )
        return s


def make_server(server_address, application):
    server = WSGIServer(server_address)
    server.set_app(application)
    return server


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit('Provide a WSGI application object as module:callable')
    app_path = sys.argv[1]
    module, application = app_path.split(':')
    module = __import__(module)
    application = getattr(module, application)

    SERVER_ADDRESS = (HOST, PORT) = '', 8888
    httpd = make_server(SERVER_ADDRESS, application)
    print('WSGIServer: Serving HTTP on port {port} ...\n'.format(port=PORT))

    httpd.serve_forever()
