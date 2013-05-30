============================
Safe Routes To School Survey
============================

http://www.masaferoutessurvey.com/

Scope: collect transportation mode and location information per child and school in anonymous parent survey

MAPC Project team: Tim Reardon, Clay Martin, Jamila Henderson, Christian Spanring

Applied GeoSolutions Project team: Matthew Hanson, Pavel Dorovskoy

Usage
=====

Execute setup.sh to install system dependencies.  

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
