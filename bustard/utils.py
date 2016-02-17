# -*- coding: utf-8 -*-
import binascii
import base64
import collections
import urllib


class MultiDict(collections.UserDict):

    def getlist(self, key):
        return self.data[key]

    def to_dict(self):
        return self.data

    def __getitem__(self, key):
        return self.data[key][-1]

    def __setitem__(self, key, value):
        if isinstance(value, (list, tuple)):
            self.data[key] = list(value)
        else:
            self.data[key] = [value]

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.data)


def json_dumps_default(obj):
    if isinstance(obj, collections.UserDict):
        return obj.to_dict()
    return obj


def parse_query_string(query_string, encoding='utf-8'):
    query_dict = collections.defaultdict(list)
    for query_item in query_string.split('&'):
        if '=' not in query_item:
            continue
        keyword, value = query_item.split('=', 1)
        value = urllib.parse.unquote_plus(value)
        query_dict[keyword].append(to_text(value, encoding=encoding))
    return query_dict


def to_header_key(key):
    return '-'.join(x.capitalize() for x in key.split('-'))


def to_text(st, encoding='utf-8'):
    if isinstance(st, str):
        return st
    elif isinstance(st, collections.ByteString):
        return st.decode(encoding)
    else:
        return str(st)


def to_bytes(bt, encoding='utf-8'):
    if isinstance(bt, collections.ByteString):
        return bt
    elif isinstance(bt, str):
        return bt.encode(encoding)
    else:
        return bytes(bt)


class Authorization:

    def __init__(self, _type, username, password):
        self.type = _type
        self.username = username
        self.password = password

    def __eq__(self, other):
        return (
            self.type == other.type and
            self.username == other.username and
            self.password == other.password
        )

    __hash__ = object.__hash__

    def __repr__(self):
        return '{}(type:{}, username:{})'.format(
            self.__class__.__name__, self.type, self.username
        )


def parse_basic_auth_header(value):
    try:
        auth_type, auth_info = to_bytes(value).split(None, 1)
    except ValueError:
        return
    auth_type = auth_type.lower()

    if auth_type == b'basic':
        try:
            username, password = base64.b64decode(auth_info).split(b':', 1)
        except (binascii.Error, ValueError):
            return

        return Authorization(
            to_text(auth_type),
            username=to_text(username),
            password=to_text(password)
        )


def cookie_date():
    pass
