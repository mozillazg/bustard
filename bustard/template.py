#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

"""简单的模板引擎"""
import re


class CodeBuilder(object):
    INDENT_STEP = 4

    def __init__(self, indent=0):
        self.code = []
        self.indent_level = indent

    def add_line(self, line):
        line = ' ' * self.indent_level + line + '\n'
        self.code.extend([line])

    def forward_indent(self):
        self.indent_level += self.INDENT_STEP

    def back_indent(self):
        self.indent_level -= self.INDENT_STEP

    def add_section(self):
        section = CodeBuilder(self.indent_level)
        self.code.append(section)
        return section

    def get_namespace(self):
        assert self.indent_level == 0
        python_code = unicode(self)
        namespace = {}
        exec(python_code, namespace)
        return namespace

    def __unicode__(self):
        return "".join(unicode(s) for s in self.code)

    def __start__(self):
        return str(self.__unicode__())


class Template(object):
    TOKEN_EXPR_START = '{{'
    TOKEN_EXPR_END = '}}'
    TOKEN_TAG_START = '{%'
    TOKEN_TAG_END = '%}'

    def __init__(self, text, context=None):
        self.context = {}
        if context is not None:
            self.context.update(context)
        self.buffered = []
        self.code = code = CodeBuilder()
        code.add_line('def render_function(context):')
        code.forward_indent()
        self.section_vars = code.add_section()  # 定义 context 内的变量
        code.add_line('result = []')

        self.tpl_text = text
        self.all_vars = set()  # 模板中出现过的变量
        self.local_vars = set()  # 模板中定义的变量
        self.parse_text(text)

    def parse_text(self, text):
        tokens = re.split(r'''(?sx)
        ({token_expr_start}.*?{token_expr_end}
        |{token_tag_start}.*?{token_tag_end})
        '''.format(token_expr_start=self.TOKEN_EXPR_START,
                   token_expr_end=self.TOKEN_EXPR_END,
                   token_tag_start=self.TOKEN_TAG_START,
                   token_tag_end=self.TOKEN_TAG_END
                   ),
            text
        )
        # express_stack = []

        for token in tokens:
            # {{ abc }}
            if token.startswith(self.TOKEN_EXPR_START):
                expr = self.strip_token(token, self.TOKEN_EXPR_START,
                                        self.TOKEN_EXPR_END).strip()

                if not ((expr.startswith('"') or expr.startswith('\''))):
                    self.all_vars.add(expr)
                if expr in self.local_vars:
                    expr = 'unicode(_%s)' % expr
                else:
                    expr = 'unicode(%s)' % expr

                self.buffered.append(expr)

            # {% blala %}
            elif token.startswith(self.TOKEN_TAG_START):
                self.flush_buffer()
                express = self.strip_token(token, self.TOKEN_TAG_START,
                                           self.TOKEN_TAG_END)
                words = express.split()
                if words[0] == 'if':
                    expr = words[1].strip()
                    self.all_vars.add(expr)

                    if expr in self.local_vars:
                        self.code.add_line('if _%s:' % expr)
                    else:
                        self.code.add_line('if %s:' % expr)
                    self.code.forward_indent()
                elif words[0] == 'for':
                    expr = words[3].strip()
                    self.all_vars.add(expr)

                    self.code.add_line('for _%s in %s:' % (words[1], expr))
                    self.local_vars.add(words[1])
                    self.code.forward_indent()
                elif words[0].startswith('end'):
                    self.code.back_indent()
            else:
                self.buffered.append('%s' % repr(token))

        for name in self.all_vars - self.local_vars:
            self.section_vars.add_line('%s = context["%s"]' % (name, name))

        self.flush_buffer()
        self.code.add_line('return "".join(result)')
        self.code.back_indent()

    def render(self, context=None):
        if context is not None:
            self.context.update(context)

        namespace = self.code.get_namespace()
        render_function = namespace['render_function']
        return render_function(context)

    def flush_buffer(self):
        self.code.add_line('result.extend([%s])' % ','.join(self.buffered))
        self.buffered = []

    def strip_token(self, text, start, end):
        text = text.replace(start, '', 1)
        text = text.replace(end, '', 1)
        return text
