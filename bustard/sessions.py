# -*- coding: utf-8 -*-
import abc
import collections
import uuid


class SessionBase(collections.UserDict):

    def __init__(self, session_key=None):
        super(SessionBase, self).__init__()
        self.session_key = session_key
        self.modified = False

    def is_empty(self):
        return not (self.session_key and self.data)

    def __setitem__(self, key, value):
        self.data[key] = value
        self.modified = True

    def __delitem__(self, key):
        del self.data[key]
        self.modified = True

    def pop(self, key, default=None):
        self.modified = self.modified or key in self.data
        return self.data.pop(key, default)

    def setdefault(self, key, value):
        if key in self.data:
            return self.data[key]
        else:
            self.modified = True
            self.data[key] = value
            return value

    def update(self, dict_):
        self.data.update(dict_)
        self.modified = True

    def clear(self):
        self.data = {}
        self.accessed = True
        self.modified = True

    def _get_or_create_session_key(self):
        if not self.session_key or not self.exists(self.session_key):
            self.session_key = self._new_session_key()
        return self.session_key

    def _new_session_key(self):
        return uuid.uuid4().hex

    @abc.abstractmethod
    def create(self):
        pass

    @abc.abstractmethod
    def exists(self, session_key=None):
        pass

    @abc.abstractmethod
    def save(self):
        pass

    @abc.abstractmethod
    def delete(self, session_key=None):
        pass


def before_request_hook(request, view_func, app):
    session_key = request.cookies.get(app.config['SESSION_COOKIE_NAME'])
    request.session = app.session_class(session_key=session_key)


def after_request_hook(request, response, view_func, app):
    session = request.session
    if not session.modified:
        return

    config = app.config
    cookie_name = config['SESSION_COOKIE_NAME']
    if session.is_empty():
        if cookie_name in request.cookies:
            session.delete()
            response.delete_cookie(cookie_name)
    else:
        session.save()
        response.set_cookie(
            cookie_name, value=session.session_key,
            max_age=config['SESSION_COOKIE_MAX_AGE'],
            expires=None, path=config['SESSION_COOKIE_PATH'],
            domain=config['SESSION_COOKIE_DOMAIN'],
            secure=config['SESSION_COOKIE_SECURE'],
            httponly=config['SESSION_COOKIE_HTTPONLY']
        )
    return response


class MemorySession(SessionBase):
    _sessions = {}

    def __init__(self, session_key=None):
        super(MemorySession, self).__init__(session_key=session_key)
        self.load(session_key)

    def load(self, session_key):
        _sessions = self.__class__._sessions
        if session_key not in _sessions:
            self.create()
        else:
            self.data = _sessions[self.session_key]

    def exists(self, key):
        _sessions = self.__class__._sessions
        return key in _sessions

    def create(self):
        self.modified = True
        self.save(must_create=True)

    def save(self, must_create=False):
        session_key = self._get_or_create_session_key()
        _sessions = self.__class__._sessions
        if self.data or must_create:
            if session_key in _sessions and not self.modified:
                self.data = _sessions[self.session_key]
            else:
                _sessions[self.session_key] = self.data
        else:
            self.delete()

    def delete(self, session_key=None):
        _sessions = self.__class__._sessions
        session_key = session_key or self.session_key
        _sessions.pop(session_key, None)
        self.modified = True
