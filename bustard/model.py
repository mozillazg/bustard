# -*- coding: utf-8 -*-


class Field:

    def __get__(self, instance, attr):
        pass

    def __set__(self, instance, attr, value):
        pass


class ModelMetaClass(type):

    def __init__(cls, *args, **kwargs):
        pass


class Model(metaclass=ModelMetaClass):
    pass


class CharField(Field):
    pass


class IntegerField(Field):
    pass


class DateField(Field):
    pass


class DateTimeField(Field):
    pass


class TextField(Field):
    pass


class BooleanField(Field):
    pass


class JSONField(Field):
    pass
