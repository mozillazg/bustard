#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from bustard.app import Bustard
from bustard.template import Template

app = Bustard()


@app.route('/')
def index():
    return 'hello'


@app.route('/template')
def tmp():
    html = Template("""
    <html>
        <h1>Hello {{ name }}</h1>
        <ul>
            {% for item in items %}
            <li> {{ item }}</li>
            {% endfor %}
        </ul>
    </html>
    """).render({'name': 'jim', 'items': ['foo', 'bar', 'foobar']})
    return html


@app.route('/hello')
def index2():
    return 403, 'hello', {'Hello-ABX': 'aaa'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
