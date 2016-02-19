# -*- coding: utf-8 -*-
from bustard.app import Bustard
from bustard.http import Response

app = Bustard()


@app.route('/')
def index(request):
    return '''
<form action="/upload" enctype="multipart/form-data" method="post">
    Username: <input type="text" name="username">
    Password: <input type="password" name="password">
    File: <input type="file" name="file">
    <input type="submit">
</form>
'''


@app.route('/upload', methods=['POST'])
def upload(request):
    _file = request.files['file']
    response = Response(_file.read(), content_type=_file.content_type)
    return response

if __name__ == '__main__':
    app.run('0.0.0.0')
