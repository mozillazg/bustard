# -*- coding: utf-8 -*-
import collections
import inspect
import os

from .constants import CONFIGURE
from .exceptions import HTTPException
from .http import Request, Response
from .router import Router
from .template import Template
from .testing import Client
from .utils import to_bytes
# from .wsgi_server import make_server
from .servers import WSGIrefServer
from . import sessions

NOTFOUND_HTML = b"""
<html>
    <h1>404 Not Found</h1>
</html>
"""


class Bustard(object):
    session_class = sessions.MemorySession
    before_request_hooks = (sessions.before_request_hook,)
    after_request_hooks = (sessions.after_request_hook,)

    def __init__(self, name='', template_dir='',
                 template_default_context=None):
        self.name = name
        self._router = Router()
        self.template_dir = template_dir
        if template_default_context is not None:
            self.template_default_context = template_default_context
        else:
            self.template_default_context = {}
        self.template_default_context.setdefault('url_for', self.url_for)

        self._before_request_hooks = []
        self._before_request_hooks.extend(self.before_request_hooks)
        self._after_request_hooks = []
        self._after_request_hooks.extend(self.after_request_hooks)

        self._config = {}
        self._config.update(CONFIGURE)

    @property
    def config(self):
        return self._config

    def render_template(self, template_name, **kwargs):
        return render_template(
            template_name, template_dir=self.template_dir,
            default_context=self.template_default_context,
            context=kwargs
        ).encode('utf-8')

    def url_for(self, func_name, _request=None, _external=False, **kwargs):
        url = self._router.url_for(func_name, **kwargs)
        if _external:
            request = _request
            url = '{}://{}{}'.format(request.scheme, request.host, url)
        return url

    def url_resolve(self, path):
        """url -> view

        :return: (func, methods, func_kwargs)
        """
        return self._router.get_func(path)

    def __call__(self, environ, start_response):
        """for wsgi server"""
        self.start_response = start_response
        path = environ['PATH_INFO']
        method = environ['REQUEST_METHOD']
        func, methods, func_kwargs = self.url_resolve(path)

        try:
            if func is None:
                self.notfound()
            if method not in methods:
                self.abort(405)
            request = Request(environ)
            result = self.handle_before_request_hooks(request, view_func=func)
            if isinstance(result, Response):
                response = result
            else:
                response = self.handle_view(request, func, func_kwargs)
            self.handle_after_request_hooks(request, response, view_func=func)
        except HTTPException as ex:
            response = ex.response

        return self._start_response(response)

    def handle_view(self, request, view_func, func_kwargs):
        result = view_func(request, **func_kwargs)
        if isinstance(result, (list, tuple)):
            response = Response(content=result[0],
                                status_code=result[1],
                                headers=result[2])
        elif isinstance(result, Response):
            response = result
        else:
            response = Response(result)
        return response

    def _start_response(self, response):
        body = response.body
        status_code = response.status
        headers_list = response.headers_list
        self.start_response(status_code, headers_list)

        if isinstance(body, collections.Iterator):
            return (to_bytes(x) for x in body)
        else:
            return [to_bytes(body)]

    def route(self, path, methods=None):

        def wrapper(func):
            self._router.register(path, func, methods)
            return func

        return wrapper

    def before_request(self, func):
        self._before_request_hooks.append(func)
        return func

    def handle_before_request_hooks(self, request, view_func):
        hooks = self._before_request_hooks
        for hook in hooks:
            if len(inspect.signature(hook).parameters) > 1:
                result = hook(request, view_func, self)
            else:
                result = hook(request)
            if isinstance(result, Response):
                return result

    def after_request(self, func):
        self._after_request_hooks.append(func)
        return func

    def handle_after_request_hooks(self, request, response, view_func):
        hooks = self._after_request_hooks
        for hook in hooks:
            if len(inspect.signature(hook).parameters) > 2:
                hook(request, response, view_func, self)
            else:
                hook(request, response)

    def notfound(self):
        raise HTTPException(Response(NOTFOUND_HTML, status_code=404))

    def abort(self, code):
        raise HTTPException(Response(status_code=code))

    def make_response(self, content=b'', **kwargs):
        if isinstance(content, Response):
            return content
        return Response(content, **kwargs)

    def test_client(self):
        return Client(self)

    def run(self, host='127.0.0.1', port=5000):
        address = (host, port)
        httpd = WSGIrefServer(host, port)
        print('WSGIServer: Serving HTTP on %s ...\n' % str(address))
        httpd.run(self)


def render_template(template_name, template_dir='', default_context=None,
                    context=None, **kwargs):
    with open(os.path.join(template_dir, template_name),
              encoding='utf-8') as f:
        return Template(f.read(), context=default_context,
                        template_dir=template_dir, **kwargs
                        ).render(**context)
