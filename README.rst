==============================
Walk Boston Parent Survey Form
==============================

http://maps.mapc.org/

Scope
=====

* Collect transportation mode and location information per child and school in anonymous survey

Dependencies
============

* Django 1.2.5 (GeoDjango)
* PostGIS

Update translations
===================

1. ``python manage.py dbgettext_export``
2. ``python manage.py makemessages -l <lang_code>``
3. ``python manage.py compilemessages``

MAPC
====

Project team: Tim Reardon, Jamila Henderson, Christian Spanring

GPL License
===========

Walk Boston Parent Survey Form is Copyright 2011 MAPC.

Walk Boston Parent Survey Form is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Walk Boston Parent Survey Form is distributed WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Walk Boston Parent Survey Form. If not, see <http://www.gnu.org/licenses/>.