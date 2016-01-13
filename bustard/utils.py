# -*- coding: utf-8 -*-
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
