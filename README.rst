============================
Safe Routes To School Survey
============================

http://www.masaferoutessurvey.com/

Scope: collect transportation mode and location information per child and school in anonymous parent survey

MAPC Project team: Tim Reardon, Clay Martin, Jamila Henderson, Christian Spanring

Applied GeoSolutions Project team: Matthew Hanson, Pavel Dorovskoy

Usage
=====

Quick setup:
This project uses Vagrant and VirtualBox to help manage time spent creating the development environment. This helps with transferability. Be sure to download Vagrant and VirtualBox. With these tools, the project can be run on any machine.
::
  $ vagrant up
  $ vagrant ssh -c "cd myschoolcommute && python manage.py runserver 0.0.0.0:8001"

Manual setup:
setup.sh is the provisioning script used for Vagrant, and provides the basis for setting up the project for Linux.

Install Python requirements

:: 

  $ pip install -r requirements.txt 

Install R requirements:

::

    $ sudo R
    > chooseCRANmirror()
    > install.packages(c("RPostgreSQL", "ggplot2", "knitr", "Hmisc", "reshape2", "plyr", "scales"))
    > q()

Update translations

::

  $ python manage.py dbgettext_export
  & python manage.py makemessages -l <lang_code>
  $ python manage.py compilemessages

----

Copyright 2013 MAPC
