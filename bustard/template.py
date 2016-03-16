# -*- coding: utf-8 -*-
"""
simple template engine

support:

* {{ foobar }}
* {{ '  foobar  '.strip() }}
* {{ foo.bar }} {{ foo.hello() }}
* {{ foo['bar'] }}
* {{ sum(filter(lambda x: x > 2, numbers)) }}
* {# ... #}
* {% if xx %} {% elif yy %} {% else %} {% endif %}
* {% for x in lst %} {% endfor %}
* {% include "path/to/b.tpl" %}
* {% extends "path/to/b.tpl" %}
* {% block body %} {% endblock body %}

"""
import builtins
import os
import re

from .constants import TEMPLATE_BUILTIN_FUNC_WHITELIST
from .utils import to_text


class CodeBuilder(object):
    INDENT_STEP = 4

    def __init__(self, indent=0):
        self.source_code = []
        self.indent_level = indent

    def add_line(self, line, *args, **kwargs):
        line = line.format(*args, **kwargs)
        line = ' ' * self.indent_level + line + '\n'
        self.source_code.extend([line])

    def forward_indent(self):
        self.indent_level += self.INDENT_STEP

    def backward_indent(self):
        self.indent_level -= self.INDENT_STEP

    def _compile(self):
        assert self.indent_level == 0
        self._code = compile(str(self), '<source>', 'exec')
        return self._code

    def _exec(self, globals_dict=None, locals_dict=None):
        """exec compiled code"""
        globals_dict = globals_dict or {}
        globals_dict.setdefault('__builtins__', {})
        locals_dict = locals_dict or {}
        exec(self._code, globals_dict, locals_dict)
        return locals_dict

    def __str__(self):
        return ''.join(map(str, self.source_code))

    def __repr__(self):
        return self.__str__()


class Template(object):
    TOKEN_EXPR_START = '{{'
    TOKEN_EXPR_END = '}}'
    TOKEN_TAG_START = '{%'
    TOKEN_TAG_END = '%}'
    TOKEN_COMMENT_START = '{#'
    TOKEN_COMMENT_END = '#}'
    FUNC_WHITELIST = TEMPLATE_BUILTIN_FUNC_WHITELIST

    def __init__(self, text, context=None,
                 pre_compile=True,
                 indent=0, template_dir='',
                 func_name='__render_function',
                 result_var='__result',
                 auto_escape=True
                 ):
        self.re_tokens = re.compile(r'''(?x)(
        (?:{token_expr_start} .+? {token_expr_end})
        |(?:{token_tag_start} .+? {token_tag_end})
        |(?:{token_comment_start}.*?{token_comment_end})
        )'''.format(token_expr_start=re.escape(self.TOKEN_EXPR_START),
                    token_expr_end=re.escape(self.TOKEN_EXPR_END),
                    token_tag_start=re.escape(self.TOKEN_TAG_START),
                    token_tag_end=re.escape(self.TOKEN_TAG_END),
                    token_comment_start=re.escape(self.TOKEN_COMMENT_START),
                    token_comment_end=re.escape(self.TOKEN_COMMENT_END),
                    )
        )
        # {% extends "base.html" %}
        self.re_extends = re.compile(r'''
            ^{token_tag_start}\s+extends\s+[\'"](?P<path>[^\'"]+)[\'"]\s+
            {token_tag_end}
        '''.format(
            token_tag_start=re.escape(self.TOKEN_TAG_START),
            token_tag_end=re.escape(self.TOKEN_TAG_END),
        ), re.VERBOSE)
        # {% block header %}...{% endblock header %}
        self.re_block = re.compile(r'''
            {token_tag_start}\s+block\s+(?P<name>\w+)\s+{token_tag_end}
            (?P<code>.*?)
            {token_tag_start}\s+endblock(?:\s+\1)?\s+{token_tag_end}
        '''.format(
            token_tag_start=re.escape(self.TOKEN_TAG_START),
            token_tag_end=re.escape(self.TOKEN_TAG_END),
        ), re.DOTALL | re.VERBOSE)
        # {{ block.super }}
        self.re_block_super = re.compile(r'''
            {token_expr_start}\s+block\.super\s+
            {token_expr_end}
        '''.format(
            token_expr_start=re.escape(self.TOKEN_EXPR_START),
            token_expr_end=re.escape(self.TOKEN_EXPR_END),
        ), re.VERBOSE)

        self.context = {
            k: v
            for k, v in builtins.__dict__.items()
            if k in self.FUNC_WHITELIST
        }
        self.context.update({
            'escape': escape,
            'noescape': noescape,
            'to_text': noescape,
        })
        if context is not None:
            self.context.update(context)
        self.base_dir = template_dir
        self.func_name = func_name
        self.result_var = result_var
        self.auto_escape = auto_escape

        self.buffered = []   # store common string
        self.code = code = CodeBuilder(indent=indent)
        # def func_name():
        #     result = []
        code.add_line('def {}():', func_name)
        code.forward_indent()
        code.add_line('{} = []', self.result_var)

        self.tpl_text = text
        self.parse_text(text)

    def parse_text(self, text):
        # if has extends, replace parent template with current blocks
        extends_text = self.handle_extends(text)
        if extends_text is not None:
            return self.parse_text(extends_text)

        tokens = self.re_tokens.split(text)

        for token in tokens:
            # common string
            if not self.re_tokens.match(token):
                self.buffered.append('{}'.format(repr(token)))
            # comment {# ... #}
            elif token.startswith(self.TOKEN_COMMENT_START):
                continue
            # {{ abc }}
            elif token.startswith(self.TOKEN_EXPR_START):
                express = self.strip_token(token, self.TOKEN_EXPR_START,
                                           self.TOKEN_EXPR_END).strip()
                if self.auto_escape:
                    self.buffered.append('escape({})'.format(express))
                else:
                    self.buffered.append('to_text({})'.format(express))

            # {% blala %}
            elif token.startswith(self.TOKEN_TAG_START):
                self.flush_buffer()
                express = self.strip_token(token, self.TOKEN_TAG_START,
                                           self.TOKEN_TAG_END).strip()
                words = express.split()
                tag_name = words[0]
                # {% if xxx %}, {% elif xxx %}, {% for xxx %}
                if tag_name in ('if', 'elif', 'for'):
                    if tag_name in ('elif',):
                        self.code.backward_indent()

                    self.code.add_line('{}:', express)
                    self.code.forward_indent()

                # {% else %}
                elif tag_name in ('else',):
                    self.code.backward_indent()
                    self.code.add_line('{}:', tag_name)
                    self.code.forward_indent()

                elif tag_name.startswith('end'):  # {% endif %}, {% endfor %}
                    self.code.backward_indent()
                    self.flush_buffer()

                elif tag_name in ('include',):
                    # parse included template file
                    # def func_name():    # current
                    #     result = []
                    #     ...
                    #     def func_name_inclued():   # included
                    #         result_included = []
                    #         ...
                    #         return ''.join(result_included)
                    #     result.append(func_name_inclued())
                    #     return ''.join(result)
                    path = ''.join(words[1:]).strip().strip('\'"')
                    _template = self.handle_include(path)
                    self.code.source_code.append(_template.code)
                    self.code.add_line(
                        '{0}.append({1}())',
                        self.result_var, _template.func_name
                    )

        self.flush_buffer()
        self.code.add_line('return "".join({})', self.result_var)
        self.code.backward_indent()

    def handle_extends(self, text):
        """replace all blocks in extends with current blocks"""
        match = self.re_extends.match(text)
        if match:
            extra_text = self.re_extends.sub('', text, count=1)
            blocks = self.get_blocks(extra_text)
            path = os.path.join(self.base_dir, match.group('path'))
            with open(path, encoding='utf-8') as fp:
                return self.replace_blocks_in_extends(fp.read(), blocks)
        else:
            return None

    def get_blocks(self, text):
        return {
            name: code
            for (name, code) in self.re_block.findall(text)
        }

    def replace_blocks_in_extends(self, extends_text, blocks):
        def replace(match):
            name = match.group('name')
            old_code = match.group('code')
            code = blocks.get(name) or old_code
            # {{ block.super }}
            return self.re_block_super.sub(old_code, code)
        return self.re_block.sub(replace, extends_text)

    def render(self, **context):
        self.code._compile()
        globals_dict = {
            '__builtins__': self.context,
        }
        globals_dict.update(context)
        namespace = self.code._exec(globals_dict, {})
        self.render_function = namespace[self.func_name]

        html = self.render_function()
        return self.cleanup_extra_whitespaces(html)

    def handle_include(self, path):
        path = os.path.join(self.base_dir, path)
        _hash = str(hash(path)).replace('-', '_').replace('.', '_')
        func_name = self.func_name + _hash
        result_var = self.result_var + _hash

        with open(path, encoding='utf-8') as f:
            _template = self.__class__(
                f.read(), context=self.context,
                pre_compile=False, indent=self.code.indent_level,
                template_dir=self.base_dir,
                auto_escape=self.auto_escape,
                func_name=func_name, result_var=result_var
            )
            return _template

    def flush_buffer(self):
        """flush all buffered string into code"""
        self.code.add_line('{0}.extend([{1}])',
                           self.result_var, ','.join(self.buffered)
                           )
        self.buffered = []

    def strip_token(self, text, start, end):
        """{{ a }} -> a"""
        text = text.replace(start, '', 1)
        text = text.replace(end, '', 1)
        return text

    def cleanup_extra_whitespaces(self, text):
        """cleanup extra whitespaces let numbers of whitespaces <=1"""
        return re.sub(r'(\s)\s+', r'\1', text)


class NoEscapedText:

    def __init__(self, raw_text):
        self.raw_text = raw_text


html_escape_table = {
    '&': '&amp;',
    '"': '&quot;',
    '\'': '&apos;',
    '>': '&gt;',
    '<': '&lt;',
}


def html_escape(text):
    return ''.join(html_escape_table.get(c, c) for c in text)


def escape(text):
    if isinstance(text, NoEscapedText):
        return to_text(text.raw_text)
    else:
        text = to_text(text)
        return html_escape(text)


def noescape(text):
    return NoEscapedText(text)
