UNIVIE LECTURES TO GOOGLE-CALENDAR
==================================

A Web application for creating google calender events, using the google 
calendar API, and iCal calendars out of UniVie course numbers.
Requirements: python2.x and all dependencies.

Command prompt arguments:
  -h, --help	 Displays instructions
  -c, --course	 Sets the course number, found in the top left corner of a course in the course overview
  -s, --semester	 Sets the semester (for example S2013 for summer semester 2013)
  -l, --language	 Language selection (must be de or en)
The command line tool does not support Google Calendar!

Example:

./univie2ical -c "260080" -l "de" -s "S2013"

DEPENDENCIES
============

* python2-google-api-python-client
* python-oauth

IMPLEMENTED SO FAR
==================

* Course parser
* iCal exporter

TODO
====
* Webinterface + Google Calendar interface
