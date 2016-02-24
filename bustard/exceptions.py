# -*- coding: utf-8 -*-
from .constants import NOTFOUND_HTML
from .http import Response


class HTTPException(Exception):
    def __init__(self, response):
        self.response = response


class NotFound(HTTPException):
    def __init__(self):
        self.response = Response(NOTFOUND_HTML, status_code=404)
