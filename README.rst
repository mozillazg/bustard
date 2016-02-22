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

``pip install bustard``


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
