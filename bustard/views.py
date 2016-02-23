# -*- coding: utf-8 -*-

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
