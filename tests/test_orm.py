# -*- coding: utf-8 -*-
import os

import pytest

from bustard import orm

pg_uri = os.environ.get(
    'BUSTARD_TEST_PG_URI',
    'postgresql://dbuser:password@localhost/exampledb'
)


@pytest.yield_fixture
def model():
    yield orm.Model
    orm.MetaData.tables = {}
    orm.MetaData.indexes = []


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
    field = getattr(orm, fieldclass)(name='name')
    assert field.to_sql() == 'name {}'.format(data_type)


@pytest.mark.parametrize('kwargs, to_sql', [
    ({'max_length': 10}, 'field_name varchar(10)'),
    ({'server_default': '\'\''}, 'field_name varchar DEFAULT \'\''),
    ({'unique': True}, 'field_name varchar UNIQUE'),
    ({'nullable': False}, 'field_name varchar NOT NULL'),
    ({'primary_key': True}, 'field_name varchar PRIMARY KEY'),
    ({'foreign_key': orm.ForeignKey('users.id')},
     'field_name varchar REFERENCES users (id)'),
])
def test_field_option(model, kwargs, to_sql):
    field = orm.CharField(name='field_name', **kwargs)
    assert field.to_sql() == to_sql


def test_define_model(model):

    class User(orm.Model):
        __tablename__ = 'users'
        id = orm.AutoField(primary_key=True)
        username = orm.CharField(max_length=80, default='',
                                 server_default="''", index=True)
        password = orm.CharField(max_length=200, default='',
                                 server_default="''")
        is_actived = orm.BooleanField(default=False, server_default=False)
        description = orm.TextField(default='', server_default="''")

    assert User.table_sql() == '''
CREATE TABLE users (
    id serial PRIMARY KEY,
    username varchar(80) DEFAULT '',
    password varchar(200) DEFAULT '',
    is_actived boolean DEFAULT FALSE,
    description text DEFAULT ''
);
'''

    assert (
        orm.MetaData.index_sqls() ==
        'CREATE INDEX index_users_username ON users (username);'
    )


@pytest.yield_fixture
def model_context():
    class User(orm.Model):
        __tablename__ = 'users'

        id = orm.AutoField(primary_key=True)
        username = orm.CharField(max_length=80, default='',
                                 server_default="''", index=True)
        password = orm.CharField(max_length=200, default='',
                                 server_default="''")
        is_actived = orm.BooleanField(default=False, server_default=False)
        description = orm.TextField(default='', server_default="''")

        def __repr__(self):
            return '<User: {}>'.format(self.id)

    engine = orm.Engine(pg_uri)
    session = orm.Session(engine)
    models = {
        'User': User,
        'engine': engine,
        'session': session,
    }
    orm.MetaData.create_all(engine)
    yield models
    session.rollback()
    session.close()
    orm.MetaData.drop_all(engine)
    orm.MetaData.tables = {}
    orm.MetaData.indexes = []


def create_user(User, session):
    user = User(username='test', password='passwd', is_actived=True)
    session.insert(user)
    return user


class TestSession:

    def test_insert(self, model_context):
        User = model_context['User']
        session = model_context['session']
        user = create_user(User, session)
        session.commit()
        assert user.id == 1

    def test_update(self, model_context):
        User = model_context['User']
        session = model_context['session']
        user = create_user(User, session)
        session.commit()
        # old_username = user.username
        user.username = 'new name'
        session.update(user)
        session.commit()

    def test_delete(self, model_context):
        User = model_context['User']
        session = model_context['session']
        user = create_user(User, session)
        session.commit()
        assert user.id == 1
        session.delete(user)
        session.commit()
        assert user.id is None

    def test_transaction(self, model_context):
        User = model_context['User']
        session = model_context['session']
        with session.transaction():
            create_user(User, session)
        session.rollback()
        assert session.query(User).filter(id=1).count() == 1

    def test_transaction_exception(self, model_context):
        User = model_context['User']
        session = model_context['session']
        with pytest.raises(AssertionError):
            with session.transaction():
                create_user(User, session)
                assert 0 > 1
        assert session.query(User).filter(id=1).count() == 0


class TestQuerySet:

    def users(self, User, session):
        return [
            create_user(User, session),
            create_user(User, session),
            create_user(User, session),
            create_user(User, session),
        ]

    def test_select(self, model_context):
        User = model_context['User']
        session = model_context['session']
        self.users(User, session)
        session.commit()

        queryset = session.query(User).filter()
        assert len(queryset) == 4
        assert queryset[1].id == 2

    def test_select_lt(self, model_context):
        User = model_context['User']
        session = model_context['session']
        self.users(User, session)
        session.commit()

        queryset = session.query(User).filter(User.id < 2)
        assert queryset.count() == 1
        assert [us.id for us in queryset] == [1]

    def test_select_le(self, model_context):
        User = model_context['User']
        session = model_context['session']
        self.users(User, session)
        session.commit()

        queryset = session.query(User).filter(User.id <= 2)
        assert queryset.count() == 2
        assert [us.id for us in queryset] == [1, 2]

    def test_select_eq(self, model_context):
        User = model_context['User']
        session = model_context['session']
        self.users(User, session)
        session.commit()

        queryset = session.query(User).filter(User.id == 2)
        assert queryset.count() == 1
        assert [us.id for us in queryset] == [2]

        queryset = session.query(User).filter(id=2)
        assert queryset.count() == 1
        assert [us.id for us in queryset] == [2]

    def test_select_gt(self, model_context):
        User = model_context['User']
        session = model_context['session']
        self.users(User, session)
        session.commit()

        queryset = session.query(User).filter(User.id > 2)
        assert queryset.count() == 2
        assert [us.id for us in queryset] == [3, 4]

    def test_select_ge(self, model_context):
        User = model_context['User']
        session = model_context['session']
        self.users(User, session)
        session.commit()

        queryset = session.query(User).filter(User.id >= 2)
        assert queryset.count() == 3
        assert [us.id for us in queryset] == [2, 3, 4]

    def test_select_is(self, model_context):
        User = model_context['User']
        session = model_context['session']
        self.users(User, session)
        session.commit()

        queryset = session.query(User).filter(User.is_actived.is_(True))
        assert queryset.count() == 4

    def test_select_isnot(self, model_context):
        User = model_context['User']
        session = model_context['session']
        self.users(User, session)
        session.commit()

        queryset = session.query(User).filter(User.is_actived.is_not(False))
        assert queryset.count() == 4

    def test_select_in(self, model_context):
        User = model_context['User']
        session = model_context['session']
        self.users(User, session)
        session.commit()

        queryset = session.query(User).filter(User.id.in_((1, 2)))
        assert queryset.count() == 2
        assert [us.id for us in queryset] == [1, 2]

    def test_select_notin(self, model_context):
        User = model_context['User']
        session = model_context['session']
        self.users(User, session)
        session.commit()

        queryset = session.query(User).filter(User.id.not_in((1, 2)))
        assert queryset.count() == 2
        assert [us.id for us in queryset] == [3, 4]

    def test_select_limit(self, model_context):
        User = model_context['User']
        session = model_context['session']
        self.users(User, session)
        session.commit()

        queryset = session.query(User).filter().limit(1)
        assert len(queryset) == 1
        assert [us.id for us in queryset] == [1]

    def test_select_offset(self, model_context):
        User = model_context['User']
        session = model_context['session']
        self.users(User, session)
        session.commit()

        queryset = session.query(User).filter().limit(1).offset(2)
        assert len(queryset) == 1
        assert [us.id for us in queryset] == [3]

    def test_update(self, model_context):
        User = model_context['User']
        session = model_context['session']
        self.users(User, session)
        session.commit()

        assert session.query(User).filter(is_actived=False).count() == 0
        session.query(User).filter(User.id > 2).update(is_actived=False)
        session.commit()
        assert session.query(User).filter(is_actived=False).count() == 2

    def test_delete(self, model_context):
        User = model_context['User']
        session = model_context['session']
        self.users(User, session)
        session.commit()

        queryset = session.query(User).filter(User.id > 2)
        assert len(queryset) == 2
        queryset.delete()
        session.commit()
        assert len(queryset) == 0
