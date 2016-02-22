# -*- coding: utf-8 -*-
import abc
import wsgiref.simple_server

from . import wsgi_server


class ServerInterface(metaclass=abc.ABCMeta):
    def __init__(self, host='127.0.0.1', port=5000, **options):
        self.host = host
        self.port = port
        self.options = options

    @abc.abstractmethod
    def run(self, app):
        pass


class BustardServer(ServerInterface):

    def run(self, app):
        httpd = wsgi_server.make_server(
            (self.host, self.port), app, **self.options
        )
        httpd.serve_forever()


class WSGIrefServer(ServerInterface):

    def run(self, app):
        httpd = wsgiref.simple_server.make_server(
            self.host, self.port, app, **self.options
        )
        httpd.serve_forever()


class WerkzeugfServer(ServerInterface):

    def run(self, app):
        from werkzeug.serving import run_simple
        run_simple(self.host, self.port, app, self.options)
