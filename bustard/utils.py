# -*- coding: utf-8 -*-
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
        if not isinstance(value, (list, tuple)):
            self.data[key] = [value]
        else:
            self.data[key] = value

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
        query_dict[keyword].append(urllib.parse.unquote_plus(value))
    return query_dict


def to_header_key(key):
    return '-'.join(x.capitalize() for x in key.split('-'))


def to_text(s, encoding='utf-8'):
    if isinstance(s, str):
        return s
    elif isinstance(s, collections.ByteString):
        return s.decode(encoding)
    else:
        return str(s)


def to_bytes(b, encoding='utf-8'):
    if isinstance(b, collections.ByteString):
        return b
    elif isinstance(b, str):
        return b.encode(encoding)
    else:
        return bytes(b)


class Authorization:

    def __init__(self, _type, data_dict):
        self.type = _type
        self.username = data_dict.get('username')
        self.password = data_dict.get('password')


def parse_basic_auth_header(value):
    auth_type, auth_info = to_bytes(value).split(None, 1)
    auth_type = auth_type.lower()
    if auth_type == b'basic':
        username, password = base64.b64decode(auth_info).split(b':', 1)
        return Authorization(auth_type, {'username': to_text(username),
                                         'password': to_text(password)})
