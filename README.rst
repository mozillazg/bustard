bustard
-----------

.. image:: https://travis-ci.org/mozillazg/bustard.svg?branch=master
    :target: https://travis-ci.org/mozillazg/bustard

A tiny web framework powered by Python.


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
    pip install psycopg2      # if need orm feature


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
