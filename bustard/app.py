#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import

import collections
import os

from .http import Request, Response, response_status_string
from .router import Router
from .template import Template
from .wsgi_server import make_server

NOTFOUND_HTML = """
<html>
    <h1>404 Not Found</h1>
</html>
"""
ResponseData = collections.namedtuple(
    'ResponseData', 'status body headers_list'
)


class Bustard(object):
    def __init__(self, name='', template_dir='',
                 template_default_context=None):
        self.name = name
        self._route = Router()
        self.template_dir = template_dir
        if template_default_context is not None:
            self.template_default_context = template_default_context
        else:
            self.template_default_context = {}
        self.template_default_context.setdefault('url_for', self.url_for)
        self._before_request_hooks = []
        self._after_request_hooks = []

    def render_template(self, template_name, **kwargs):
        return render_template(
            template_name, template_dir=self.template_dir,
            default_context=self.template_default_context,
            context=kwargs
        ).encode('utf-8')

    def url_for(self, func_name, **kwargs):
        return self._route.url_for(func_name, **kwargs)

    def __call__(self, environ, start_response):
        """for wsgi server"""
        self.start_response = start_response
        path = environ['PATH_INFO']
        method = environ['REQUEST_METHOD']
        func, methods, func_kwargs = self._route.get_func(path)
        if func is None:
            return self.notfound()
        if method not in methods:
            return self.abort(405)

        self.request = Request(environ)
        response_args = self.handle_view(self.request, func, func_kwargs)
        return self.make_response(body=response_args.body,
                                  code=response_args.status,
                                  headers=response_args.headers_list)

    def handle_view(self, request, view_func, func_kwargs):
        response = view_func(request, **func_kwargs)
        if isinstance(response, (list, tuple)):
            return ResponseData(*response)
        elif isinstance(response, Response):
            return self._dump_response(response)
        else:
            return ResponseData(200, response, None)

    def _dump_response(self, response):
        status = response.status
        body = response.content
        headers_list = response.headers.items()
        cookies = response.cookies
        for cookie in cookies.values():
            for value in cookie.values():
                headers_list.append(('Set-Cookie', value.OutputString()))
        return ResponseData(status, body, headers_list)

    def make_response(self, body, code=200, headers=None,
                      content_type='text/html; charset=utf-8'):
        if isinstance(body, str):
            body = body.encode('utf-8')

        if isinstance(code, int):
            status_code = response_status_string(code)
        else:
            status_code = str(code)

        if isinstance(headers, dict):
            headers.setdefault('Content-Type', content_type)
            headers_list = headers.items()
        elif isinstance(headers, collections.Iterable):
            headers_list = headers
        else:
            headers_list = (('Content-Type', content_type),)
        self.start_response(status_code, headers_list)
        return [body]

    def route(self, path, methods=None):

        def wrapper(func):
            self._route.register(path, func, methods)
            return func

        return wrapper

    def before_request(self, func):
        self._before_request_hooks.append(func)
        return func

    def after_request(self, func):
        self._after_request_hooks.append(func)
        return func

    def notfound(self):
        return self.make_response(NOTFOUND_HTML, code=404)

    def abort(self, code):
        return self.make_response(b'', code=code)

    def run(self, host='127.0.0.1', port=5000):
        address = (host, port)
        httpd = make_server(address, self)
        print('WSGIServer: Serving HTTP on %s ...\n' % str(address))
        httpd.serve_forever()


def render_template(template_name, template_dir='', default_context=None,
                    context=None, **kwargs):
    with open(os.path.join(template_dir, template_name),
              encoding='utf-8') as f:
        return Template(f.read(), context=default_context,
                        template_dir=template_dir, **kwargs
                        ).render(context=context)
