# -*- coding: utf-8 -*-
import abc
import collections

_tables = collections.OrderedDict()
_indexes = []


class Field(metaclass=abc.ABCMeta):
    def __init__(self, name=None, max_length=None, default=None,
                 server_default=None, unique=False, nullable=True,
                 index=False, primary_key=False, foreign_key=None):
        self.name = name
        self.max_length = max_length
        self.default = default
        if server_default is True or server_default is False:
            server_default = str(server_default).upper()
        self.server_default = server_default
        self.unique = unique
        self.nullable = nullable
        self.index = index
        self.primary_key = primary_key
        self.foreign_key = foreign_key

    def __get__(self, instance, attr):
        return instance.__dict__[attr]

    def __set__(self, instance, attr, value):
        instance.__dict__[attr] = value

    def to_sql(self):
        sql = '{0.name} {0.data_type}'.format(self)
        if self.max_length is not None:
            sql += '({0.max_length})'.format(self)
        if self.server_default:
            sql += ' DEFAULT {0.server_default}'.format(self)
        if not self.nullable:
            sql += ' NOT NULL'
        if self.unique:
            sql += ' UNIQUE'
        if self.primary_key:
            sql += ' PRIMARY KEY'
        if self.foreign_key is not None:
            sql += ' {}'.format(self.foreign_key.to_sql())
        return sql


def _collect_fields(attr_dict):
    fields = []
    for attr_value in attr_dict.values():
        if isinstance(attr_value, Field):
            fields.append(attr_value)
    return fields


def _get_table_name(attr_dict):
    return attr_dict.get('__tablename__')


def _auto_column_name(attr_dict):
    for attr, attr_value in attr_dict.items():
        if isinstance(attr_value, Field):
            if attr_value.name is None:
                attr_value.name = attr


def _collect_indexes(table_name, attr_dict):
    indexes = []
    for attr, attr_value in attr_dict.items():
        if isinstance(attr_value, Field):
            if not any([attr_value.unique, attr_value.primary_key,
                        attr_value.foreign_key]) and attr_value.index:
                indexes.append(attr_value)
    for field in indexes:
        column_name = field.name
        name = 'index_{}_{}'.format(table_name, column_name)
        index = Index(name, table_name, column_name, unique=field.unique)
        _indexes.append(index)


class ModelMetaClass(type):

    def __init__(cls, name, bases, attr_dict):
        table_name = _get_table_name(attr_dict)
        if table_name:
            cls._table_name = table_name
            cls._fields = _collect_fields(attr_dict)
            _tables[cls._table_name] = cls
            _auto_column_name(attr_dict)
            _collect_indexes(table_name, attr_dict)

    @classmethod
    def __prepare__(cls, name, bases):
        """让 attr_dict 有序"""
        return collections.OrderedDict()


class Model(metaclass=ModelMetaClass):

    @classmethod
    def table_sql(cls):
        column_sqls = ',\n    '.join(field.to_sql() for field in cls._fields)
        sql = '''
CREATE TABLE {table_name} (
    {column_sqls}
);
'''.format(table_name=cls._table_name, column_sqls=column_sqls)
        return sql


class CharField(Field):
    data_type = 'varchar'

    def __init__(self, max_length=None, **kwargs):
        super(CharField, self).__init__(max_length=max_length, **kwargs)


class IntegerField(Field):
    data_type = 'integer'


class DateField(Field):
    data_type = 'date'


class DateTimeField(Field):
    data_type = 'timestamp'


class TextField(Field):
    data_type = 'text'


class BooleanField(Field):
    data_type = 'boolean'


class UUIDField(Field):
    data_type = 'uuid'


class JSONField(Field):
    data_type = 'json'


class AutoField(Field):
    data_type = 'serial'


class ForeignKey:
    """

    :param column: A single target column for the key relationship.
                   A column name as a string: `table_name.column_name`
    :param onupdate: Optional string. If set, emit ON UPDATE <value>
                     when issuing DDL for this constraint. Typical values
                     include CASCADE, DELETE and RESTRICT.
    :param ondelete: Optional string. If set, emit ON DELETE <value>
                     when issuing DDL for this constraint. Typical values
                     include CASCADE, DELETE and RESTRICT.
    """
    def __init__(self, column, onupdate=None, ondelete=None):
        self.table_name, self.column_name = column.split('.')
        self.onupdate = onupdate
        self.ondelete = ondelete

    def to_sql(self):
        sql = 'REFERENCES {0.table_name} ({0.column_name})'.format(self)
        if self.onupdate:
            sql += ' ON UPDATE {0.onupdate}'.format(self)
        if self.ondelete:
            sql += ' ON DELETE {0.ondelete}'.format(self)
        return sql


class Index:
    def __init__(self, name, table_name, column_name, unique=False):
        self.name = name
        self.table_name = table_name
        self.column_name = column_name
        self.unique = unique

    def to_sql(self):
        sql = 'CREATE'
        if self.unique:
            sql += ' UNIQUE'
        sql += (' INDEX {0.name} ON {0.table_name} ({0.column_name})'
                ).format(self)
        return sql + ';'


def index_sqls():
    sqls = []
    for index in _indexes:
        sqls.append(index.to_sql())
    return ';\n'.join(sqls)
