# -*- coding: utf-8 -*-
import mimetypes
import os

from .exceptions import NotFound
from .http import Response

http_methods = ('get', 'post', 'head', 'options',
                'delete', 'put', 'trace', 'patch')


class View:
    decorators = ()

    def dispatch_request(self, request, *args, **kwargs):
        method = request.method.lower()
        if method == 'head' and not hasattr(self, 'head'):
            method = 'get'
        view_func = getattr(self, method)
        return view_func(request, *args, **kwargs)

    @classmethod
    def as_view(cls, name=None, *class_args, **class_kwargs):

        def view(request, *args, **kwargs):
            instance = view.view_class(*class_args, **class_kwargs)
            return instance.dispatch_request(request, *args, **kwargs)

        for decorator in cls.decorators:
            view = decorator(view)

        view.view_class = cls
        view.__name__ = name or cls.__name__
        methods = []
        for method in http_methods:
            if hasattr(cls, method):
                methods.append(method.upper())
        methods = frozenset(methods)
        cls.methods = methods
        view.methods = methods
        return view


class StaticFilesView(View):

    def __init__(self, static_dir):
        self.static_dir = os.path.abspath(static_dir)

    def get(self, request, path):
        file_path = os.path.abspath(os.path.join(self.static_dir, path))
        if not file_path.startswith(self.static_dir):
            raise NotFound()
        if not os.path.isfile(file_path):
            raise NotFound()

        with open(file_path, 'rb') as fp:
            content = fp.read()
        content_type = mimetypes.guess_type(file_path)[0]
        content_type = content_type or 'application/octet-stream'
        return Response(content, content_type=content_type)
