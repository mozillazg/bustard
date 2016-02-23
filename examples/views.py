# -*- coding: utf-8 -*-

from bustard.app import Bustard
from bustard.views import View

app = Bustard(__name__)


class IndexView(View):

    def get(self, request, name):
        return name

    def post(self, request, name):
        return '{} post'.format(name)


app.add_url_rule('/hello/(?P<name>\w+)', IndexView.as_view())

if __name__ == '__main__':
    app.run(host='0.0.0.0')
