# -*- coding: utf-8 -*-
import collections
import inspect
import os

from .http import Request, Response, response_status_string
from .router import Router
from .template import Template
from .testing import Client
from .utils import to_bytes
from .wsgi_server import make_server

NOTFOUND_HTML = """
<html>
    <h1>404 Not Found</h1>
</html>
"""


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

    def url_for(self, func_name, _request=None, _external=False, **kwargs):
        url = self._route.url_for(func_name, **kwargs)
        if _external:
            request = _request
            url = '{}://{}{}'.format(request.scheme, request.host, url)
        return url

    def url_resolve(self, path):
        """url -> view

        :return: (func, methods, func_kwargs)
        """
        return self._route.get_func(path)

    def __call__(self, environ, start_response):
        """for wsgi server"""
        self.start_response = start_response
        path = environ['PATH_INFO']
        method = environ['REQUEST_METHOD']
        func, methods, func_kwargs = self.url_resolve(path)
        if func is None:
            return self.notfound()
        if method not in methods:
            return self.abort(405)

        request = Request(environ)
        result = self.handle_before_request_hooks(request, view_func=func)
        if isinstance(result, Response):
            response = result
        else:
            response = self.handle_view(request, func, func_kwargs)
        self.handle_after_request_hooks(request, response, view_func=func)

        return self._make_response(body=response.body,
                                   code=response.status_code,
                                   headers=response.headers_list)

    def handle_view(self, request, view_func, func_kwargs):
        result = view_func(request, **func_kwargs)
        if isinstance(result, (list, tuple)):
            response = Response(content=result[1],
                                status_code=result[0],
                                headers=result[2])
        elif isinstance(result, Response):
            response = result
        else:
            response = Response(result)
        return response

    def _make_response(self, body, code=200, headers=None,
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

        if isinstance(body, collections.Iterator):
            return (to_bytes(x) for x in body)
        else:
            return [body]

    def route(self, path, methods=None):

        def wrapper(func):
            self._route.register(path, func, methods)
            return func

        return wrapper

    def before_request(self, func):
        self._before_request_hooks.append(func)
        return func

    def handle_before_request_hooks(self, request, view_func):
        hooks = self._before_request_hooks
        for hook in hooks:
            if len(inspect.signature(hook).parameters) > 1:
                result = hook(request, view_func)
            else:
                result = hook(request, view_func)
            if isinstance(result, Response):
                return result

    def after_request(self, func):
        self._after_request_hooks.append(func)
        return func

    def handle_after_request_hooks(self, request, response, view_func):
        hooks = self._after_request_hooks
        for hook in hooks:
            if len(inspect.signature(hook).parameters) > 2:
                hook(request, response, view_func)
            else:
                hook(request, response)

    def notfound(self):
        return self._make_response(NOTFOUND_HTML, code=404)

    def abort(self, code):
        return self._make_response(b'', code=code)

    def make_response(self, content=b'', *args, **kwargs):
        if isinstance(content, Response):
            return content
        return Response(content, *args, **kwargs)

    def test_client(self):
        return Client(self)

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
                        ).render(**context)
