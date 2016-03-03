ChangeLog
----------


0.1.4 (2016-03-03)
====================

* [new] template engine support extends
* [improve] refactoring template engine
* [bugfix] fix WerkzeugfServer.run
* [improve] don't connect to db when init orm.Session instance


0.1.3 (2016-02-27)
====================

* [improve] refactoring template engine
* [bugfix] fix orm.queryset.count: don't include limit and offset in sql
* [improve] improve orm.session.connect: auto reconnect
* [bugfix] fix testing about post form
* [new] testing.open support ``follow_redirects=False`` argument


0.1.2 (2016-02-26)
====================

* [new] add views.View and app.add_url_rule
* [new] remove psycopg2 from setup.py
* [new] add views.StaticFilesView
* [new] add orm.session.transaction
* [change] rename ServerInterface to ServerAdapter
* [change] rename WSGIrefServer to WSGIRefServer


0.1.1 (2016-02-22)
====================

* [bugfix] fix a session key issue
* [change] refactoring ServerInterface


0.1.0 (2016-02-19)
====================

* Initial Release
