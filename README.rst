==============================
Walk Boston Parent Survey Form
==============================

http://myschoolcommute.org/

Scope: collect transportation mode and location information per child and school in anonymous parent survey

MAPC Project team: Tim Reardon, Jamila Henderson, Christian Spanring
Applied GeoSolutions Project team: Matthew Hanson, Pavel Dorovskoy

Usage
=====

Install requirements

:: 

  $ pip install -r requirements.txt

Get submodules (bootstrap CSS framework)

::

  $ git submodule init
  $ git submodule update

Update translations

::

  $ python manage.py dbgettext_export
  & python manage.py makemessages -l <lang_code>
  $ python manage.py compilemessages

----

Copyright 2011 MAPC
