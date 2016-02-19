#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from codecs import open
import sys
import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import bustard

if sys.argv[-1] == 'publish':
    os.system('python setup.py register')
    os.system('python setup.py sdist upload')
    os.system('python setup.py bdist_wheel upload')
    sys.exit()

packages = [
    'bustard',
]

requirements = [
    'psycopg2',
]


def long_description():
    readme = open('README.rst', encoding='utf8').read()
    return readme

setup(
    name=bustard.__title__,
    version=bustard.__version__,
    description=bustard.__doc__,
    long_description=long_description(),
    url='https://github.com/mozillazg/bustard',
    author=bustard.__author__,
    author_email='mozillazg101@gmail.com',
    license=bustard.__license__,
    packages=packages,
    package_data={'': ['LICENSE']},
    package_dir={'bustard': 'bustard'},
    include_package_data=True,
    install_requires=requirements,
    zip_safe=False,
    platforms='any',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)
