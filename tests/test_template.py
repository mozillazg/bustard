#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import collections
import os

import pytest

from bustard.template import Template

current_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(current_dir, 'templates')


def echo(*args, **kwargs):
    return args, sorted(kwargs.items())


test_data = (
    # var
    ('{{ abc }}', {'abc': 'foobar'}, 'foobar'),
    ('b{{ abc }}c', {'abc': 'foobar'}, 'bfoobarc'),
    ('{{ abc }', {'abc': 'foobar'}, '{{ abc }'),
    # comment
    ('{# abc #}', {'abc': 'foobar'}, ''),
    # index
    ('{{ abc[1] }}', {'abc': [1, 2]}, '2'),
    # key
    ('{{ abc["key"] }}', {'abc': {'key': 'eg'}}, 'eg'),
    # dot
    ('{{ abc.key }}', {'abc': collections.namedtuple('abc', 'key')('你好')},
     '你好'),
    # func
    ('{{ echo(1, 2, 3, a=1, b=a) }}', {'echo': echo, 'a': 4},
     '((1, 2, 3), [(&apos;a&apos;, 1), (&apos;b&apos;, 4)])'),

    # if
    ('{% if abc %}true{% endif %}', {'abc': True}, 'true'),
    ('{% if "a" in abc %}true{% endif %}', {'abc': 'aa'}, 'true'),
    ('{% if a in abc %}true{% endif %}', {'a': 'a', 'abc': 'aa'}, 'true'),
    # if + func
    ('{% if len(abc) %}true{% endif %}', {'abc': 'abc'}, 'true'),
    ('{% if len(abc) > 1 %}true{% endif %}', {'abc': 'aa'}, 'true'),
    # if ... else ...
    ('{% if abc %}true{% else %}false{% endif %}', {'abc': ''}, 'false'),

    # if ... elif ... else
    ('{% if abc == "abc" %}true' +
     '{% elif abc == "efg" %}{{ abc }}' +
     '{% else %}false{% endif %}',
     {'abc': 'efg'}, 'efg'),

    # for x in y
    ('{% for item in items %}{{ item }}{% endfor %}',
     {'items': [1, 2, 3]}, '123'),

    ('{% for n, item in enumerate(items) %}' +
     '{{ n }}{{ item }},' +
     '{% endfor %}',
     {'items': ['a', 'b', 'c']}, '0a,1b,2c,'),

    # for + if
    ('{% for item in items %}' +
     '{% if item > 2 %}{{ item }}{% endif %}' +
     '{% endfor %}' +
     '{{ items[1] }}',
     {'items': [1, 2, 3, 4]}, '342'),

    # escape
    ('<a>{{ title }}</a>', {'title': '<a>'}, '<a>&lt;a&gt;</a>'),
    # noescape
    ('<a>{{ noescape(title) }}</a>', {'title': '<a>'}, '<a><a></a>'),

    ('{{ list(map(lambda x: x * 2, [1, 2, 3])) }}', {}, '[2, 4, 6]'),
)


@pytest.mark.parametrize(
    ('tpl', 'context', 'result'),
    test_data
)
def test_base(tpl, context, result):
    assert Template(tpl).render(**context) == result


def test_include():
    with open(os.path.join(template_dir, 'index.html')) as fp:
        template = Template(fp.read(), template_dir=template_dir)
    assert template.render(items=[1, 2, 3]) == (
        '<ul>'
        '<li>1</li>'
        '<li>2</li>'
        '<li>3</li>\n'
        '</ul>\n'
    )
