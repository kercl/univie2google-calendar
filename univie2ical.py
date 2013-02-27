#!/usr/bin/env python2
# -*- coding: iso-8859-15

from lib.univie import Event, Course
import sys

C_PARSE_NEW = 0
C_COURSE_NR = 1
C_SEM = 2
C_LANG = 3

DEBUG_MODE = True

def main(argv):
	action = C_PARSE_NEW 

	course_numbers = list()
	semester = ""
	language = "de"

	for arg in argv:
		if action == C_PARSE_NEW:
			if arg in ("-h", "--help"):
				print("University of Vienna course to iCal-file\n"+
				  "  -h, --help\t Displays this message\n"+
				  "  -c, --courses\t Comma seperated list of all courses you want to import\n"+
				  "  -s, --semester\t Sets the semester (for example S2013 for summer semester 2013)\n"+
				  "  -l, --language\t Language selection (must be de or en)\n")
				exit(0)
			elif arg in ("-c", "--course"):
				action = C_COURSE_NR
			elif arg in ("-s", "--semester"):
				action = C_SEM
			elif arg in ("-l", "--language"):
				action = C_LANG
		elif action == C_COURSE_NR:
			try:
				courses = arg.split(',')
				for c in courses:
					course_numbers.append(int(c))
			except ValueError:
				print("Error: Not all course numbers are valid")
				exit(1)
			action = C_PARSE_NEW
		elif action == C_SEM:
			semester = arg
			action = C_PARSE_NEW
		elif action == C_LANG:
			language = arg
			action = C_PARSE_NEW

	if DEBUG_MODE == False:
		print """BEGIN:VCALENDAR
	PRODID:univie2ical
	VERSION:2.0
	CALSCALE:GREGORIAN
	METHOD:PUBLISH
	X-WR-TIMEZONE:Europe/Vienna
	BEGIN:VTIMEZONE
	TZID:Europe/Vienna
	X-LIC-LOCATION:Europe/Vienna
	BEGIN:DAYLIGHT
	TZOFFSETFROM:+0100
	TZOFFSETTO:+0200
	TZNAME:CEST
	DTSTART:19700329T020000
	RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU
	END:DAYLIGHT
	BEGIN:STANDARD
	TZOFFSETFROM:+0200
	TZOFFSETTO:+0100
	TZNAME:CET
	DTSTART:19701025T030000
	RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU
	END:STANDARD
	END:VTIMEZONE"""
	for course_number in course_numbers:
		if course_number == 0:
			if DEBUG_MODE == True:
				print("Error: Invalid course: " + str(course_number))

		curc = Course(course_number, semester, language)

		for ev in curc.events:
			if DEBUG_MODE == True:
				print(ev.to_string())
			else:
				print(ev.to_ical_event())

	if DEBUG_MODE == False:
		print "END:VCALENDAR"

if __name__ == "__main__":
   main(sys.argv[1:])
