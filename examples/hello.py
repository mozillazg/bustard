# -*- coding: utf-8 -*-
from bustard.app import Bustard

app = Bustard()


@app.route('/')
def helloword(request):
    return 'hello world'

if __name__ == '__main__':
    app.run()
