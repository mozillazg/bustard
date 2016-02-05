# -*- coding: utf-8 -*-
import pytest
from bustard.model import ForeignKey


@pytest.yield_fixture
def model():
    from bustard import model
    yield model
    model._tables = {}
    model._indexes = []


@pytest.mark.parametrize('fieldclass, data_type', [
    ('CharField', 'varchar'),
    ('IntegerField', 'integer'),
    ('DateField', 'date'),
    ('DateTimeField', 'timestamp'),
    ('TextField', 'text'),
    ('BooleanField', 'boolean'),
    ('UUIDField', 'uuid'),
    ('JSONField', 'json'),
    ('AutoField', 'serial'),
])
def test_field(model, fieldclass, data_type):
    field = getattr(model, fieldclass)(name='name')
    assert field.to_sql() == 'name {}'.format(data_type)


@pytest.mark.parametrize('kwargs, to_sql', [
    ({'max_length': 10}, 'field_name varchar(10)'),
    ({'server_default': '\'\''}, 'field_name varchar DEFAULT \'\''),
    ({'unique': True}, 'field_name varchar UNIQUE'),
    ({'nullable': False}, 'field_name varchar NOT NULL'),
    ({'primary_key': True}, 'field_name varchar PRIMARY KEY'),
    ({'foreign_key': ForeignKey('users.id')},
     'field_name varchar REFERENCES users (id)'),
])
def test_field_option(model, kwargs, to_sql):
    field = model.CharField(name='field_name', **kwargs)
    assert field.to_sql() == to_sql


def test_define_model(model):

    class User(model.Model):
        __tablename__ = 'users'
        id = model.AutoField(primary_key=True)
        username = model.CharField(max_length=80, default='',
                                   server_default='""', index=True)
        password = model.CharField(max_length=200, default='',
                                   server_default='""')
        is_actived = model.BooleanField(default=False, server_default=False)
        description = model.TextField(default='', server_default='""')

    assert User.table_sql() == '''
CREATE TABLE users (
    id serial PRIMARY KEY,
    username varchar(80) DEFAULT "",
    password varchar(200) DEFAULT "",
    is_actived boolean DEFAULT FALSE,
    description text DEFAULT ""
);
'''

    assert (
        model.index_sqls() ==
        'CREATE INDEX index_users_username ON users (username);'
    )
