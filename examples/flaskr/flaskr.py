# -*- coding: utf-8 -*-
import os

from bustard.app import Bustard
from bustard.http import redirect
from bustard.orm import (
    Engine, Model, MetaData, Session,
    AutoField, TextField
)
from bustard.views import StaticFilesView


class Entry(Model):
    __tablename__ = 'entries'

    id = AutoField(primary_key=True)
    title = TextField()
    content = TextField(default='', server_default="''")


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(CURRENT_DIR, 'templates')
STATIC_DIR = os.path.join(CURRENT_DIR, 'static')
USERNAME = 'admin'
PASSWORD = 'passwd'
PG_URI = 'postgresql://dbuser:password@localhost/example_bustardr'
engine = Engine(PG_URI)
session = Session(engine)
app = Bustard(__name__, template_dir=TEMPLATE_DIR)
app.add_url_rule('/static/<path>',
                 StaticFilesView.as_view(static_dir=STATIC_DIR))


def init_db():
    MetaData.create_all(engine)


def drop_db():
    MetaData.drop_all(engine)


@app.route('/')
def show_entries(request):
    entries = session.query(Entry).filter()
    return app.render_template('show_entries.html', entries=entries,
                               session=request.session)


@app.route('/add', methods=['POST'])
def add_entry(request):
    if not request.session.get('logged_in'):
        app.abort(401)
    entry = Entry(title=request.form['title'],
                  content=request.form['content'])
    session.insert(entry)
    session.commit()
    return redirect(app.url_for('show_entries'))


@app.route('/login', methods=['GET', 'POST'])
def login(request):
    error = None
    if request.method == 'POST':
        if request.form['username'] != USERNAME:
            error = 'Invalid username'
        elif request.form['password'] != PASSWORD:
            error = 'Invalid password'
        else:
            request.session['logged_in'] = True
            return redirect(app.url_for('show_entries'))
    return app.render_template('login.html', error=error,
                               session=request.session)


@app.route('/logout')
def logut():
    session.pop('logged_in', None)
    return redirect(app.url_for('show_entries'))

if __name__ == '__main__':
    app.run()
