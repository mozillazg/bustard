# -*- coding: utf-8 -*-
import collections
import re
import urllib


class Router(object):
    def __init__(self):
        self._urls_regex_map = {}
        self._urls_builer_map = {}

    def register(self, path, func, methods=None):
        url_builder = URLBuilder(path)
        url_match_re = re.compile(url_builder.url_regex)

        methods = set([x.upper() for x in methods or ['GET']])
        if 'GET' in methods and 'HEAD' not in methods:
            methods.add('HEAD')

        FuncPair = collections.namedtuple('FuncPair', ('func', 'methods'))
        self._urls_regex_map[url_match_re] = FuncPair(func, methods)
        self._urls_builer_map[url_builder] = FuncPair(func, methods)

    def get_func(self, path):
        """
        :return: (func, methods)
        """
        for url_match, func_pair in self._urls_regex_map.items():
            m = url_match.match(path)
            if m is not None:
                return func_pair.func, func_pair.methods, m.groupdict()
        return None, None, None

    def url_for(self, func_name, **kwargs):
        for url_builder, func_pair in self._urls_builer_map.items():
            func = func_pair.func
            if func.__name__ == func_name:
                return url_builder.build_url(**kwargs)
        return ''


class URLBuilder(object):
    # /<int:id>
    RE_PATH_TYPE = re.compile(r'''<
    (?:(?P<type>int|float|path):)?
    (?P<name>\w+)
    >''', re.X)
    TYPE_REGEX_MAP = {
        'int': r'\d+',
        'float': r'\d+(?:\.\d+)?',
        'path': r'.+',
    }
    # /(?P<id>\d+)
    RE_PATH_REGEX = re.compile(r'''
    \(\?P<
    (?P<name>\w+)
    >[^\)]+
    \)''', re.X)

    def __init__(self, url_exp):
        self.url_format, self.url_kwarg_names = self.exp_to_format(url_exp)
        self.url_regex = self.exp_to_regex(url_exp)

    @classmethod
    def exp_to_format(cls, exp):
        names = set()
        if cls.RE_PATH_TYPE.search(exp) or cls.RE_PATH_REGEX.search(exp):

            def replace(m):
                name = m.group('name')
                names.add(name)
                return '{' + name + '}'

            exp = cls.RE_PATH_REGEX.sub(replace, exp)
            exp = cls.RE_PATH_TYPE.sub(replace, exp)
        return exp, names

    @classmethod
    def exp_to_regex(cls, exp):
        if not exp.startswith('^'):
            if exp.startswith('/'):
                exp = '^' + exp
            else:
                exp = '^/' + exp
        if not exp.endswith('$'):
            exp = exp + '$'

        # /<int:id>
        if '(?P<' not in exp and cls.RE_PATH_TYPE.search(exp):
            exp = cls.RE_PATH_TYPE.sub(cls._replace_type_to_regex, exp)
        return exp

    @classmethod
    def _replace_type_to_regex(cls, match):
        """ /<int:id>  -> r'(?P<id>\d+)' """
        groupdict = match.groupdict()
        _type = groupdict.get('type')
        type_regex = cls.TYPE_REGEX_MAP.get(_type, '[^/]+')
        name = groupdict.get('name')
        return r'(?P<{name}>{type_regex})'.format(
            name=name, type_regex=type_regex
        )

    def build_url(self, **kwargs):
        unknown_names = set(kwargs.keys()) - self.url_kwarg_names
        url = self.url_format.format(**kwargs)
        if unknown_names:
            url += '?' + urllib.parse.urlencode(
                {k: kwargs[k] for k in unknown_names}
            )
        return url

    def __repr__(self):
        return r'<URLBuilder; url_format: {!r}>'.format(self.url_format)

    def __hash__(self):
        return hash(self.url_regex)
