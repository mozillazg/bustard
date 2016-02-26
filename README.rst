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


usage
==============

::

    from bustard.app import Bustard

    app = Bustard()


    @app.route('/')
    def helloword(request):
        return 'hello world'

    if __name__ == '__main__':
        app.run()


.. |Build| image:: https://img.shields.io/travis/mozillazg/bustard/master.svg
   :target: https://travis-ci.org/mozillazg/bustard
.. |Coverage| image:: https://img.shields.io/coveralls/mozillazg/bustard/master.svg
   :target: https://coveralls.io/r/mozillazg/bustard
.. |PyPI version| image:: https://img.shields.io/pypi/v/bustard.svg
   :target: https://pypi.python.org/pypi/bustard
