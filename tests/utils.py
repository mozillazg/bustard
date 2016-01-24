# -*- coding: utf-8 -*-
import types


def copy_func(func, name=None):
    new_func = types.FunctionType(
        func.__code__, func.__globals__,
        name or func.__name__,
        func.__defaults__, func.__closure__
    )
    new_func.__dict__.update(func.__dict__)
    return new_func
