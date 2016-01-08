#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import collections
import operator


class Router(object):
    def __init__(self):
        self.methods = collections.defaultdict(list)
        self.methods.update({
            'GET': [],
            'POST': [],
            'PUT': [],
            'HEAD': [],
            'PATCH': [],
            'DELETE': [],
            'OPTIONS': [],
        })

    def register(self, path, func, methods=None):
        methods = [x.upper() for x in methods or ['GET']]
        for method in methods:
            self.methods[method].append((path, func))

    def get_func(self, path, method):
        for p, func in self.methods[method]:
            if p == path:
                return func

    def url_for(self, func_name):
        values = reduce(operator.add, self.methods.values())
        for path, func in values:
            if func.__name__ == func_name:
                return path
