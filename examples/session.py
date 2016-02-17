# -*- coding: utf-8 -*-
from bustard.app import Bustard

app = Bustard()


@app.route('/set/<value>')
def set_session(request, value):
    request.session['name'] = value
    return 'hello {}'.format(value)


@app.route('/')
def get_session(request):
    value = request.session.get('name', '')
    return 'hello {}'.format(value)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
