# -*- coding: utf-8 -*-
from collections import OrderedDict

import pytest

from bustard.router import Router
from .utils import copy_func
router = Router()


def func_a(): pass
func_b = copy_func(func_a, 'func_b')
func_c = copy_func(func_a, 'func_c')
func_d = copy_func(func_a, 'func_d')
func_e = copy_func(func_a, 'func_e')
func_f = copy_func(func_a, 'func_f')
func_g = copy_func(func_a, 'func_g')
func_h = copy_func(func_a, 'func_h')
func_i = copy_func(func_a, 'func_i')
func_j = copy_func(func_a, 'func_j')
router.register('/a', func_a, methods=['GET', 'POST'])
router.register('/b/c/', func_b, methods=['DELETE', 'POST'])
router.register('/c/d/f', func_c, methods=['PATCH', 'PUT'])
# regex
router.register('/d/(?P<id>\d+)', func_d, methods=['GET'])
router.register('/e/(?P<id>\d+)', func_e, methods=['POST'])
router.register('/f/(?P<id>\d+)/(?P<code>\w+)', func_f, methods=['GET'])
# /<int:id>
router.register('/g/<id>', func_g, methods=['GET', 'POST'])
router.register('/h/<int:id>', func_h, methods=['GET', 'PUT'])
router.register('/i/<float:id>', func_i, methods=['GET', 'POST'])
router.register('/j/<path:path>', func_j, methods=['PUT', 'POST'])


@pytest.mark.parametrize('path, func_name, methods, kwargs', [
    # /path
    ('/a', 'func_a', {'GET', 'POST', 'HEAD'}, {}),
    ('/a/b', None, None, None),
    ('/b/c/', 'func_b', {'DELETE', 'POST'}, {}),
    ('/b/c/d', None, None, None),
    ('/c/d/f', 'func_c', {'PATCH', 'PUT'}, {}),
    ('/c/d/g', None, None, None),
    # regex
    ('/d/1', 'func_d', {'GET', 'HEAD'}, {'id': '1'}),
    ('/d/a', None, None, None),
    ('/e/2', 'func_e', {'POST'}, {'id': '2'}),
    ('/e/e', None, None, None),
    ('/f/3/c', 'func_f', {'GET', 'HEAD'}, {'id': '3', 'code': 'c'}),
    ('/f/3/c/d', None, None, None),
    # /<int:id>, /<float:id>, /<path:path>
    ('/g/e', 'func_g', {'GET', 'POST', 'HEAD'}, {'id': 'e'}),
    ('/h/8', 'func_h', {'GET', 'PUT', 'HEAD'}, {'id': '8'}),
    ('/h/a', None, None, None),
    ('/i/2.3', 'func_i', {'GET', 'POST', 'HEAD'}, {'id': '2.3'}),
    ('/i/a', None, None, None),
    ('/j/a/b/c/', 'func_j', {'PUT', 'POST'}, {'path': 'a/b/c/'}),
    ('/j/', None, None, None),
])
def test_get_func(path, func_name, methods, kwargs):
    assert router.get_func(path) == (
        (globals()[func_name] if func_name is not None else None),
        methods,
        kwargs
    )


@pytest.mark.parametrize('func_name, kwargs, path', [
    # /path
    ('func_a', {}, '/a'),
    ('func_a', OrderedDict([('a', 'b'), ('c', 1)]), '/a?a=b&c=1'),
    ('func_b', {}, '/b/c/'),
    ('func_c', {}, '/c/d/f'),
    # regex
    ('func_d', {'id': 1}, '/d/1'),
    ('func_e', {'id': 2}, '/e/2'),
    ('func_f', {'id': 3, 'code': 'c'}, '/f/3/c'),
    ('func_f', {'id': 3, 'code': 'c', 'k': 'v'}, '/f/3/c?k=v'),
    # /<int:id>, /<float:id>, /<path:path>
    ('func_g', {'id': 'e'}, '/g/e'),
    ('func_h', {'id': 8}, '/h/8'),
    ('func_i', {'id': 2.3}, '/i/2.3'),
    ('func_j', {'path': 'a/b/c/'}, '/j/a/b/c/'),
    ('func_abc', {}, ''),
])
def test_url_for(func_name, kwargs, path):
    assert router.url_for(func_name, **kwargs) == path
