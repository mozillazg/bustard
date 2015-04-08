#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from bustard.app import Bustard

app = Bustard()


@app.route('/')
def index():
    return 'hello'


@app.route('/hello')
def index2():
    return 403, 'hello', {'Hello-ABX': 'aaa'}

if __name__ == '__main__':
    app.run()
