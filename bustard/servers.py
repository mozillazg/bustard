# -*- coding: utf-8 -*-
import abc
import wsgiref.simple_server

from . import wsgi_server


class ServerInterface(metaclass=abc.ABCMeta):
    def __init__(self, app):
        self.app = app

    @abc.abstractmethod
    def run(self, host='127.0.0.1', port=5000, **kwargs):
        pass


class BustardServer(ServerInterface):

    def run(self, host='127.0.0.1', port=5000, **kwargs):
        httpd = wsgi_server.make_server((host, port), self.app)
        httpd.serve_forever()


class WsgirefServer(ServerInterface):

    def run(self, host='127.0.0.1', port=5000, **kwargs):
        httpd = wsgiref.simple_server.make_server(host, port, self.app)
        httpd.serve_forever()


class WerkzeugfServer(ServerInterface):

    def run(self, host='127.0.0.1', port=5000, **kwargs):
        from werkzeug.serving import run_simple
        run_simple(host, port, self.app, **kwargs)
