bustard
-----------

|Build| |Coverage| |Pypi version|

A tiny WSGI web framework.


features
===============

* router
* orm
* request and response
* cookies and session
* template
* wsgi server

install
=============

::

    pip install bustard
    pip install psycopg2      # if you need orm feature


Getting Started
===================

::

    from bustard.app import Bustard

    app = Bustard()


    @app.route('/')
    def helloword(request):
        return 'hello world'

    if __name__ == '__main__':
        app.run()

Just save it as hello.py and run it ::

    $ python hello.py
    WSGIServer: Serving HTTP on ('127.0.0.1', 5000) ...

Now visit http://localhost:5000, and you should see ``hello world``.


.. |Build| image:: https://img.shields.io/travis/mozillazg/bustard/master.svg
   :target: https://travis-ci.org/mozillazg/bustard
.. |Coverage| image:: https://img.shields.io/coveralls/mozillazg/bustard/master.svg
   :target: https://coveralls.io/r/mozillazg/bustard
.. |PyPI version| image:: https://img.shields.io/pypi/v/bustard.svg
   :target: https://pypi.python.org/pypi/bustard
