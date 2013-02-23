UNIVIE LECTURES TO GOOGLE-CALENDAR
==================================

A script for creating google calender events, using the google 
calendar API, from course numbers of the University of Vienna.
You need to install python2.x and all dependencies.
Tested only with physics and mathematics lectures!

Command prompt arguments:
  -h, --help	 Displays instructions
  -c, --course	 Sets the course number, found in the top left corner of a course in the course overview
  -s, --semester	 Sets the semester (for example S2013 for summer semester 2013)
  -l, --language	 Language selection (must be de or en)
  -g, --gcal	 Specifies the google calendar identifier

Example:

./univie2gcal -c 260080 -g "somegmailaddress@gmail.com" -s "S2013"

DEPENDENCIES
============

python2-google-api-python-client
python-oauth
