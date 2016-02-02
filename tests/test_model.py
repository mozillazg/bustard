# -*- coding: utf-8 -*-
import pytest


@pytest.yield_fixture
def model():
    from bustard import model
    yield model
    model.__tables = {}
    model.__indexes = []


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


def test_charfield_max_length(model):
    field_a = model.CharField(name='field', max_length=10)
    assert field_a.to_sql() == 'field varchar(10)'
