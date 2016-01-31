# -*- coding: utf-8 -*-


class HTTPException(Exception):
    def __init__(self, response):
        self.response = response
