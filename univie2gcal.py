#!/usr/bin/env python2
# -*- coding: iso-8859-15

import urllib
import sys
import xml.etree.ElementTree as xml
import string
import re

C_PARSE_NEW = 0
C_COURSE_NR = 1
C_SEM = 2
C_LANG = 3

"""BEGIN:VCALENDAR
PRODID:univie2gcal
VERSION:2.0
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:Physik
X-WR-TIMEZONE:Europe/Vienna
BEGIN:VTIMEZONE
TZID:Europe/Vienna
X-LIC-LOCATION:Europe/Vienna
END:VTIMEZONE


END:VCALENDAR
"""

class Event:
	T_STANDALONE = 1
	T_REFERENCE = 2
	T_RELATIVE = 3
	
	title = None
	dateStart = None
	recurrence = None
	frequency = None
	dateUntil = None
	day = None
	description = None
	location = None
	timeStart = None
	timeEnd = None
	
	eventType = T_STANDALONE

	def time_to_str(self, arr, rfc3339 = False):
		if "hour" not in arr or "minute" not in arr:
			return ""
		
		if rfc3339:
			return "%(hour)02d%(minute)02d00" % {"hour" : arr['hour'], "minute" : arr['minute']}
		return "%(hour)02d:%(minute)02d" % {"hour" : arr['hour'], "minute" : arr['minute']}

	def date_to_str(self, arr, rfc3339 = False):
		if "day" not in arr or "month" not in arr or "year" not in arr:
			return ""
		
		if rfc3339:
			return "%(y)04d%(m)02d%(d)02d" % {"d" : arr['day'], "m" : arr['month'], 'y' : arr['year']}
		return "%(d)02d.%(m)02d.%(y)04d" % {"d" : arr['day'], "m" : arr['month'], 'y' : arr['year']}

	def ToICalEvent(self, course):
		event = "BEGIN:VEVENT\n"
		if self.dateStart != None:
			event = event + "DTSTART:" + self.date_to_str(self.dateStart) + "T" + self.time_to_str(self.timeStart, True) + "\n"
			event = event + "DTEND:" + self.date_to_str(self.dateStart) + "T" + self.time_to_str(self.timeEnd, True) + "\n"
		if self.recurrence != None and self.dateUntil != None and self.day != None:
			event = event + "RRULE:FREQ=" + self.recurrence
			event = event + ";UNTIL=" + self.date_to_str(self.dateUntil, True) + "T" + self.time_to_str(self.timeEnd, True)
			event = event + ";BYDAY=" + self.day + "\n"
		if self.description != None:
			event = event + "DESCRIPTION:" + self.description
		if self.location != None:
			event = event + "LOCATION:" + self.location
		if self.timeStart != None:
			event = event + "DTSTART:" + self.time_to_str(self.timeStart, True)
		if self.timeEnd != None:
			event = event + "DTEND:" + self.time_to_str(self.timeEnd, True)
		
		event = event + str(self.title)
	
	def __str__(self):
		ret = "Event: \t\t" + str(self.title) + "\n"
		ret = ret + "Date: \t\t" + self.date_to_str(self.dateStart) + "\n"
		ret = ret + "Until: \t\t" + self.date_to_str(self.dateUntil) + "\n"
		ret = ret + "Location: \t" + self.location + "\n"
		ret = ret + "Frequency: \t" + str(self.frequency) + "\n"
		ret = ret + "Recurrence: \t" + str(self.recurrence) + "\n"
		ret = ret + "Time: \t\t" + self.time_to_str(self.timeStart) + " - " + self.time_to_str(self.timeEnd) + "\n"
		ret = ret + "Description: \t" + str(self.description) + "\n"
		ret = ret + "\n"
		return ret

class Course:
	is_valid = None
	
	courseId = 0
	
	events = list()
	
	C_INIT = -1
	C_DATE = 1
	C_FREQ = 2
	C_DAY = 3
	C_LOCATION = 4
	C_TIME_INTERVAL = 5
	C_DATE_BEG = 6
	C_DATE_END = 7
	C_IGNORE_UNTIL_DAY = 8
	C_TIME = 9
	C_END = 999
	
	parser_decisions = {-1 : (C_INIT, [0, 14]),
						 0 : (C_DAY, [1,2,11,0]),
						 1 : (C_FREQ, [3]),
						 2 : (C_DATE, [4, 15]),
						 3 : ("von", [5]),
						 4 : (C_TIME_INTERVAL, [13, 9, 10]),
						 5 : (C_DATE, [6]),
						 6 : ("bis", [2]),
						 9 : ("Ort:", [10]),
						 10: (C_LOCATION, [C_END]),
						 11: ("jeweils", [12]),
						 12: ("von", [4]),
						 13: ("Uhr", [10]),
						 14: ("Vorbesprechung:", [2]),
						 15: (C_TIME, [13]),
						 C_END: (C_END, [])}
	
	#private:
	
	current_meeting = {}
	special_meeting = {}
	date_until = False
	
	def clean(self, arg, first_alphanum = False, encode = True):
		if len(arg) == 0:
			return ""
		
		arg = ' '.join(arg.split())
		
		if first_alphanum:
			while arg[0] not in string.ascii_lowercase + string.ascii_uppercase + string.digits and len(arg) > 0:
				arg = ' '.join(arg[1:].split())

		if encode:
			return arg.encode('utf-8')
		else:
			return arg
	
	def close_div_tags(self, s):
		
		d = 0
		for i in range(0, len(s)):
			if s[i:i+5] in ("<div " or "<div>"):
				d = d + 1
			if s[i:i+6] == "</div>":
				d = d - 1
		if d < 0:
			d = 0
		return s + "</div>" * d
	
	def extract_content(self, page):
		entry_pt = page.find('<div id="content">');
		exit_pt = -1
		d = 0;
		for i in range(entry_pt, len(page)):
			if page[i:i+5] in ("<div " or "<div>"):
				d = d + 1
			if page[i:i+6] == "</div>":
				d = d - 1
			if d == 0:
				exit_pt = i + 6
				break
		
		if entry_pt > exit_pt or exit_pt < 0:
			return None
	
		if page[entry_pt:exit_pt].find('<!-- vlvz_gruppe -->') != -1:
			groups = page[entry_pt:exit_pt].split('<!-- vlvz_gruppe -->')
		else:
			return [xml.fromstring('<?xml version="1.0" encoding="ISO-8859-15"?>\n' + page[entry_pt:exit_pt])]

		res = list()
		for i in range(1,len(groups)):
			res.append(xml.fromstring('<?xml version="1.0" encoding="ISO-8859-15"?>\n' + self.close_div_tags(groups[0] + groups[i])));

		return res
	
	def match(self, txt, mtype):
		if mtype == self.C_DATE:
			m = re.match(r'(\d+).(\d+).(\d+)', txt)
			if m != None:
				return {"day" : int(m.group(1)), "month" : int(m.group(2)), "year" : int(m.group(3))}
		elif mtype == self.C_TIME_INTERVAL:
			m = re.match(r'(\d+)[.:](\d+)-(\d+)[.:](\d+)', txt)
			if m != None:
				return [{"hour" : int(m.group(1)), "minute" : int(m.group(2))}, {"hour" : int(m.group(3)), "minute" : int(m.group(4))}]
		elif mtype == self.C_TIME:
			m = re.match(r'(\d+)[.:](\d+)', txt)
			if m != None:
				return {"hour" : int(m.group(1)), "minute" : int(m.group(2))}
		
		txt = txt.replace(',', '')
		if mtype == self.C_DAY:
			days = ["MO", "DI", "MI", "DO", "FR", "SA", "SO", "Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
			if txt in days:
				return ["MO", "TU", "WE", "TH", "FR", "SA", "SO", "MO", "TU", "WE", "TH", "FR", "SA", "SO"][days.index(txt)]
		elif mtype == self.C_FREQ:
			if txt in ("wtl", u"wöchtentlich"):
				return "WEEKLY"
			if txt in ("14-tg"):
				return "WEEKLY2"
		elif type(mtype) is str:
			return txt == mtype
		return None

	def rec_parse(self, tokens, it, state_id):
		state = self.parser_decisions[state_id]
		
		if it == len(tokens) or state[0] == self.C_END:
			#DBG: print "   [PARSER FINISHED]"
			return it
		
		if state[0] == self.C_INIT:
			it = it - 1
			#DBG: print "ENTERING STATE: " + str(state_id) + " => " + str(state)
		else:
			t = tokens[it]
			
			#DBG: print "ENTERING STATE: " + str(state_id) + " => " + str(state) + " - TOKEN{" + t + "}"
			
			m = self.match(t, state[0])
			if m == None or m == False:
				if state[0] == self.C_LOCATION:
					if self.match(t, self.C_DAY) != None:
						return self.rec_parse(tokens, it, self.C_END);
					self.current_meeting[self.C_LOCATION] = self.current_meeting[self.C_LOCATION] + " " + t
					return self.rec_parse(tokens, it + 1, state_id)
				else:
					#DBG: print "   [STATE INVALID]"
					return False
			else:
				if state[0] == self.C_DATE:
					if self.date_until == False:
						self.current_meeting[self.C_DATE_BEG] = m
					else:
						self.current_meeting[self.C_DATE_END] = m
						self.date_until = False
				elif state[0] == self.C_DAY:
					""" --- """
					##self.current_meeting[self.C_DAY].append = m
				elif type(m) is not bool:
					self.current_meeting[state[0]] = m
				elif t == 'bis':
					self.date_until = True
		
		for s in state[1]:
			r = self.rec_parse(tokens, it + 1, s)
			if r != False:
				return r
		
	
	def parse_meetings(self, txt):
		txt = txt.replace(';', '')
		
		self.current_meeting[self.C_LOCATION] = ""
		
		tokens = txt.split()
		
		nexti = 0
		
		parsed_meeting = []
		while nexti < len(tokens):
			self.current_meeting = {}
			self.date_until = False
			
			self.current_meeting[self.C_LOCATION] = ""
			self.current_meeting[self.C_DAY] = []
			nexti = self.rec_parse(tokens, nexti, -1)
			
			if nexti == None:
				#DBG: print "PARSER FAILED"
				return []
			
			parsed_meeting.append(self.current_meeting)
		
		return parsed_meeting

			
		
	
	def parse_course_information(self, page):
		content_groups = self.extract_content(page)
		
		if content_groups == None:
			return
		
		for content in content_groups:
			comment = ""
			event = ""
			lecturer = ""
			pmeetings = []
			for div in content.iter('div'):
				if 'class' in div.attrib:
					if div.attrib['class'] == 'vlvz_kurzkommentar':
						for text in div.itertext():
							comment = comment + text
					elif div.attrib['class'] == 'vlvz_vortragende':
						for text in div.itertext():
							lecturer = lecturer + text
					elif div.attrib['class'] == 'vlvz_termine':
						mtxt = "";
						for text in div.itertext():
							mtxt = mtxt + text
						pmeetings = self.parse_meetings(mtxt)
					elif div.attrib['class'] == 'vlvz_langtitel':
						event = div.find('abbr').text;
						titel_item = div.find('span');
						if 'class' in titel_item.attrib:
							if titel_item.attrib['class'] == 'vlvz_titel':
								event = event + ": " + titel_item.text
			if lecturer != "":
				lecturer = "(" + self.clean(lecturer, encode=True) + ")"
			
			for pm in pmeetings:
				ev = Event()
				ev.description = self.clean(comment, first_alphanum = True) + " " + self.clean(lecturer)
				ev.title = self.clean(event)
				if self.C_DATE_BEG in pm:
					ev.dateStart = pm[self.C_DATE_BEG]
				if self.C_DATE_END in pm:
					ev.dateUntil = pm[self.C_DATE_END]
				if self.C_LOCATION in pm:
					ev.location = self.clean(pm[self.C_LOCATION])
				if self.C_FREQ in pm:
					ev.frequency = pm[self.C_FREQ]
				if self.C_TIME_INTERVAL in pm:
					ev.timeStart = pm[self.C_TIME_INTERVAL][0]
					ev.timeEnd = pm[self.C_TIME_INTERVAL][1]
				
				self.events.append(ev)

		return
		
	def __init__(self, cnr, sem, lang="de"):
		params = urllib.urlencode({'lang': lang, 
		                           'semester' : sem,
		                           'lvnr': cnr})
		f = urllib.urlopen("http://online.univie.ac.at/vlvz?%s" % params)
		print "\n=======================================================\n"
		self.courseId = cnr
		self.parse_course_information(f.read())

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
				courses = arg.split(';')
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
	
	for course_number in course_numbers:
		print("Importing " + str(course_number));
		if course_number == 0:
			print("Error: No valid course or google calendar specified")
		
		curc = Course(course_number, semester, language)
		
		for ev in curc.events:
			print ev

if __name__ == "__main__":
   main(sys.argv[1:])
