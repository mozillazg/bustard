# -*- coding: utf-8 -*-
import os

import pytest

current_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.yield_fixture
def current_dir():
    yield current_dir
