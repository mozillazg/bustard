#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import pytest

from bustard.template import Template


test_data = (
    ('{{ abc }}', {'abc': 'foobar'}, 'foobar'),
    ('{# abc #}', {'abc': 'foobar'}, ''),
    ('{% if abc %}true{% endif %}', {'abc': True}, 'true'),
    ('{% if abc %}true{% else %}false{% endif %}', {'abc': ''}, 'false'),

    ('{% if abc == "abc" %}true' +
     '{% elif abc == "efg" %}{{ abc }}' +
     '{% else %}false{% endif %}',
     {'abc': 'efg'}, 'efg'),

    ('{% for item in items %}{{ item }}{% endfor %}',
     {'items': [1, 2, 3]}, '123'),

    ('{% for n, item in enumerate(items) %}' +
     '{{ n }}{{ item }},' +
     '{% endfor %}',
     {'items': ['a', 'b', 'c']}, '0a,1b,2c,'),

    ('{% for item in items %}' +
     '{% if item > 2 %}{{ item }}{% endif %}' +
     '{% endfor %}',
     {'items': [1, 2, 3, 4]}, '34'),
)


@pytest.mark.parametrize(
    ('tpl', 'context', 'result'),
    test_data
)
def test_base(tpl, context, result):
    assert Template(tpl).render(context) == result
