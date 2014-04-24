sqlautocode
===========

Effort discontinued. Have switched to <a href="https://pypi.python.org/pypi/sqlacodegen">sqlacodegen</a> which is cleaner, does a better job at generating model, and works using SQLAlchemy >= 0.9 and Python 3. You can view my fork of the project <a href="https://github.com/ksindi/sqlacodegen">here</a>.

---

Made some modifications to config.py and declarative.py to get object relationships to work.

Have also fixed issue 42. http://code.google.com/p/sqlautocode/issues/detail?id=42

Note that sqlautocode doesn't generate relationships for tables where overlapping composite foreign keys exist.

---

http://code.google.com/p/sqlautocode/
ORIGINAL README.md

AutoCode is a flexible tool to autogenerate a model from an existing database.

This is a slightly different approach to SqlSoup, 
that lets you use tables without explicitly defining them.

Current Maintainer:
    
    Chris Perkins (percious)
    E-mail: chris@percious.com

    Simon Pamies (spamsch)
    E-Mail: s.pamies at banality dot de

Authors:

    Paul Johnson (original author)
    
    Christophe de Vienne (cdevienne)
    E-Mail: cdevienne at gmail dot com

    Svilen Dobrev (sdobrev)
    E-Mail: svilen_dobrev at users point sourceforge dot net
    
License:
    
    MIT
    see license.txt

Requirements:

    sqlalchemy 0.6+

Documentation:

    Call sqlautocode.py --help for a list of available self explaining options.

    Example:
    sqlautocode.py -o model.py -u postgres://postgres:user@password/MyDatabase -s myschema -t Person*,Download

ToDo:

    + Generate ActiveMapper / Elixir model

Notes (random):

    ATT: sqlautocode currently does not handle function indexes well. It generates
    code not understood by sqlalchemy.

    (old) metadata stuff from:
    http://sqlzoo.cn/howto/source/z.dir/tip137084/i12meta.xml
