# -*- coding: utf-8 -*-
import os

from bustard.app import Bustard
from bustard.views import StaticFilesView

app = Bustard(__name__)
current_dir = os.path.dirname(os.path.abspath(__file__))
app.add_url_rule('/static/<path>',
                 StaticFilesView.as_view(static_dir=current_dir))

if __name__ == '__main__':
    app.run()
