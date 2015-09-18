#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

"""
简单的模板引擎

支持

* 直接输出变量：{{ foobar }}
* if 语句：{% if True %} {% endif %}
* for 循环：{% for x in lst %} {% endfor %}

"""
from copy import deepcopy
import re


class CodeBuilder(object):
    # 缩进步长
    INDENT_STEP = 4

    def __init__(self, indent=0):
        self.code = []
        # 当前缩进
        self.indent_level = indent

    def add_line(self, line):
        """增加一行代码"""
        line = ' ' * self.indent_level + line + '\n'
        self.code.extend([line])

    def forward_indent(self):
        """缩进前进一步"""
        self.indent_level += self.INDENT_STEP

    def back_indent(self):
        """缩进后退一步"""
        self.indent_level -= self.INDENT_STEP

    def add_section(self):
        """申请一个基于当前缩进的代码块"""
        section = CodeBuilder(self.indent_level)
        self.code.append(section)
        return section

    def _compile(self):
        """编译生成的代码"""
        assert self.indent_level == 0
        self._code = compile(unicode(self), '<source>', 'exec')
        return self._code

    def get_namespace(self):
        """执行生成的代码"""
        namespace = {}
        exec(self._code, namespace)
        return namespace

    def __unicode__(self):
        return "".join(unicode(s) for s in self.code)

    def __str__(self):
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

        # 定义 context 内的变量
        self.section_vars = code.add_section()
        # 将函数内的执行结果保存在 result 中
        code.add_line('result = []')

        self.tpl_text = text
        # 模板中出现过的全局变量
        self.global_vars = set()
        # 模板中定义的变量
        self.tmp_vars = set()

        # 解析模板
        self.parse_text(text)

        # 编译生成的代码
        self.code._compile()
        namespace = self.code.get_namespace()
        self.render_function = namespace['render_function']

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
                global_var = self.strip_token(token, self.TOKEN_EXPR_START,
                                              self.TOKEN_EXPR_END).strip()
                global_var = self.collect_var(global_var)

                self.buffered.append('unicode(%s)' % self.wrap_var(global_var))

            # {% blala %}
            elif token.startswith(self.TOKEN_TAG_START):
                self.flush_buffer()
                express = self.strip_token(token, self.TOKEN_TAG_START,
                                           self.TOKEN_TAG_END)
                words = express.split()
                if words[0] == 'if':
                    global_var = self.collect_var(words[1])

                    self.code.add_line('if %s:' % self.wrap_var(global_var))
                    self.code.forward_indent()

                elif words[0] == 'for':
                    tmp_var = self.collect_tmp_var(words[1])
                    global_var = self.collect_var(words[3])

                    self.code.add_line('for _%s in %s:'
                                       % (tmp_var, global_var))
                    self.code.forward_indent()

                elif words[0].startswith('end'):
                    self.code.back_indent()

            else:
                self.buffered.append('%s' % repr(token))

        # 定义模板中用到的全局变量
        for name in (self.global_vars - self.tmp_vars):
            self.section_vars.add_line('%s = context["%s"]' % (name, name))

        self.flush_buffer()
        self.code.add_line('return "".join(result)')
        self.code.back_indent()

    def render(self, context=None):
        """使用 context 字典渲染模板"""
        _context = deepcopy(self.context)
        if context is not None:
            _context.update(context)

        return self.render_function(_context)

    def collect_var(self, var):
        """将模板中出现的变量加入到 global_vars 中"""
        # 不处理 {{ "abc" }}
        var = var.strip()
        if not ((var.startswith('"') or var.startswith('\''))):
            self.global_vars.add(var)
        return var

    def collect_tmp_var(self, var):
        """收集循环中定义的临时变量"""
        var = var.strip()
        self.tmp_vars.add(var)
        return var

    def wrap_var(self, var):
        """处理变量, 将临时变量的名称增加 _ 前缀"""
        var = var.strip()
        if var in self.tmp_vars:
            return '_%s' % var
        else:
            self.collect_var(var)
            return var

    def flush_buffer(self):
        self.code.add_line('result.extend([%s])' % ','.join(self.buffered))
        self.buffered = []

    def strip_token(self, text, start, end):
        text = text.replace(start, '', 1)
        text = text.replace(end, '', 1)
        return text
