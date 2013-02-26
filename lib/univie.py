# -*- coding: iso-8859-15

import urllib
import xml.etree.ElementTree as xml
import string
import re
from copy import copy

class Event:
	T_STANDALONE = 1
	T_REFERENCE = 2
	T_RELATIVE = 3
	
	eventType = T_STANDALONE
	
	def __init__(self):
		self.title = None
		self.dateStart = None
		self.recurrence = None
		self.frequency = None
		self.dateUntil = None
		self.day = None
		self.description = None
		self.location = None
		self.timeStart = None
		self.timeEnd = None
		self.eventUID = None
		self.specialEvent = None
		

	def time_to_str(self, arr, rfc3339 = False):
		#print "TIME: " + str(arr) #DGG
		if arr == None:
			return "None";
		if "hour" not in arr or "minute" not in arr:
			return ""
		
		if rfc3339:
			return "%(hour)02d%(minute)02d00" % {"hour" : arr['hour'], "minute" : arr['minute']}
		return "%(hour)02d:%(minute)02d" % {"hour" : arr['hour'], "minute" : arr['minute']}

	def date_to_str(self, arr, rfc3339 = False):
		#print "DATE: " + str(arr) #DBG
		if arr == None:
			return "None";
		if "day" not in arr or "month" not in arr or "year" not in arr:
			return ""
		
		if rfc3339:
			return "%(y)04d%(m)02d%(d)02d" % {"d" : arr['day'], "m" : arr['month'], 'y' : arr['year']}
		return "%(d)02d.%(m)02d.%(y)04d" % {"d" : arr['day'], "m" : arr['month'], 'y' : arr['year']}

	def ToICalEvent(self):
		event = "BEGIN:VEVENT\n"
		if self.dateStart != None and self.timeStart != None and self.timeEnd != None:
			event = event + "DTSTART;TZID=Europe/Vienna:" + self.date_to_str(self.dateStart, True) + "T" + self.time_to_str(self.timeStart, True) + "Z\n"
			event = event + "DTEND;TZID=Europe/Vienna:" + self.date_to_str(self.dateStart, True) + "T" + self.time_to_str(self.timeEnd, True) + "Z\n"
		else:
			return None
		if self.frequency != None and self.dateUntil != None and self.recurrence != None:
			event = event + "RRULE:FREQ=" + self.frequency
			event = event + ";UNTIL=" + self.date_to_str(self.dateUntil, True) + "T" + self.time_to_str(self.timeEnd, True)
			event = event + ";BYDAY=" + self.recurrence + "\n"
		if self.description != None:
			event = event + "DESCRIPTION:" + self.description + "\n"
		if self.location != None:
			event = event + "LOCATION:" + self.location + "\n"
		if self.eventUID != None:
			event = event + "UID:" + self.eventUID + "\n"
		
		event = event + "SUMMARY:" + self.title + "\n" + "END:VEVENT"
		return event
	
	def __str__(self):
		ret = "Event: \t\t" + str(self.title).decode('iso-8859-15') + u"\n"
		ret = ret + u"Date: \t\t" + self.date_to_str(self.dateStart) + u"\n"
		ret = ret + u"Until: \t\t" + self.date_to_str(self.dateUntil) + u"\n"
		ret = ret + u"Location: \t" + self.location + u"\n"
		ret = ret + u"Frequency: \t" + str(self.frequency) + u"\n"
		ret = ret + u"Recurrence: \t" + str(self.recurrence) + u"\n"
		ret = ret + u"Time: \t\t" + self.time_to_str(self.timeStart) + u" - " + self.time_to_str(self.timeEnd) + u"\n"
		#ret = ret + u"Description: \t" + str(self.description).decode('iso-8859-15') + u"\n"
		ret = ret + u"\n"
		return ret.encode("utf-8")

class Course:
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
	
	C_SPECIAL_NOTE = 998
	
	parser_decisions = {-1 : (C_INIT, [0, 14]),
						 0 : (C_DAY, [1,2,11,4,0]),
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
						 14: ("Vorbesprechung:", [2, 16]),
						 15: (C_TIME, [13]),
						 16: (C_IGNORE_UNTIL_DAY, [C_END]),
						 C_END: (C_END, [])}
	
	def clean(self, arg, first_alphanum = False):
		if len(arg) == 0:
			return ""
		
		arg = ' '.join(arg.split())
		
		if first_alphanum:
			while arg[0] not in string.ascii_lowercase + string.ascii_uppercase + string.digits and len(arg) > 0:
				arg = ' '.join(arg[1:].split())
		
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
		page = page.replace("&nbsp;", " ")
		
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
			txt = txt.replace(',', '')
			m = txt.split('.')
			if len(m) == 3:
				try:
					date = {"day" : int(m[0]), "month" : int(m[1]), "year" : int(m[2])}
				except ValueError:
					return None
				return date
			return None
		elif mtype == self.C_TIME_INTERVAL:
			txt = txt.replace(',', '')
			s = txt.split('-')
			if len(s) == 2:
				d1 = re.split('[.:]', s[0])
				d2 = re.split('[.:]', s[1])
				if len(d1) == 2 and len(d2) == 2:
					try:
						timeinterval = [{"hour" : int(d1[0]), "minute" : int(d1[1])}, {"hour" : int(d2[0]), "minute" : int(d2[1])}]
					except:
						return None
					return timeinterval
				return None
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
		
	def is_preposition(self, txt):
		return txt in ["im", "in", "am"]
	
	def extend_time(self, tm, l=120):
		return [tm, {'minute': tm['minute']+l % 60, 'hour': tm['hour']+l / 60}]

	def rec_parse(self, tokens, it, state_id):
		state = self.parser_decisions[state_id]
		
		if it == len(tokens) or state[0] == self.C_END:
			#print "   [PARSER FINISHED]" #DBG
			return it
		
		if state[0] == self.C_INIT:
			it = it - 1
			#print "ENTERING STATE: " + str(state_id) + " => " + str(state) + " (it="+str(it)+")" #DBG
		elif state[0] == self.C_IGNORE_UNTIL_DAY:
			#print "ENTERING STATE: " + str(state_id) + " => " + str(state) + " (it="+str(it)+")" #DBG
			self.add_meeting = False
			while self.match(tokens[it], self.C_DAY) == None:
				it = it + 1
			#print "IGNORE TO " + str(it) #DBG
			return it
		else:
			t = tokens[it]
			
			#print "ENTERING STATE: " + str(state_id) + " => " + str(state) + " - TOKEN{" + t + "}" + " (it="+str(it)+")" #DBG
			
			m = self.match(t, state[0])
			#print("   [MATCH RESULT] " + str(m))
			if m == None or m == False:
				if state[0] == self.C_LOCATION:
					if it > 0:
						if self.is_preposition(tokens[it-1]) == False:
							if self.match(t, self.C_DAY) != None:
								return self.rec_parse(tokens, it, self.C_END);
					else:
						if self.match(t, self.C_DAY) != None:
								return self.rec_parse(tokens, it, self.C_END);
					if self.is_preposition(t) == False or self.current_meeting[self.C_LOCATION] != "":
						self.current_meeting[self.C_LOCATION] = self.current_meeting[self.C_LOCATION] + " " + t
					return self.rec_parse(tokens, it + 1, state_id)
				else:
					#print "   [STATE INVALID]" #DBG
					return False
			else:
				if state[0] == self.C_DATE:
					if self.date_until == False:
						self.current_meeting[self.C_DATE_BEG] = m
					else:
						self.current_meeting[self.C_DATE_END] = m
						self.date_until = False
				elif state[0] == self.C_DAY:
					self.current_meeting[self.C_DAY].append(m)
				elif state[0] == self.C_TIME:
					self.current_meeting[self.C_TIME_INTERVAL] = self.extend_time(m)
				elif type(m) is not bool:
					self.current_meeting[state[0]] = m
				elif t == 'bis':
					self.date_until = True
				elif t == 'Vorbesprechung:':
					self.is_reference = True
					self.current_meeting[self.C_SPECIAL_NOTE] = t
		
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
			special_event = ""
			self.date_until = False
			
			self.current_meeting[self.C_LOCATION] = ""
			self.current_meeting[self.C_DAY] = []
			self.add_meeting = True
			nexti = self.rec_parse(tokens, nexti, -1)
			
			if nexti == None:
				#print "   [PARSER FAILED]" #DBG
				return []
			
			if self.add_meeting:
				parsed_meeting.append(self.current_meeting)
		
		return parsed_meeting

			
		
	
	def parse_course_information(self, page):
		if page.find('<!-- notfound -->') >= 0:
			self.error = "course not found"
			return
		
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
				lecturer = "(" + self.clean(lecturer) + ")"
			
			referenceEvent = None
			
			for pm in pmeetings:
				ev = Event()
				ev.description = self.clean(comment, first_alphanum = True) + " " + lecturer
				ev.title = self.clean(event)
				if self.C_DATE_BEG in pm:
					ev.dateStart = pm[self.C_DATE_BEG]
				else:
					ev.eventType = Event.T_RELATIVE
				if self.C_DATE_END in pm:
					ev.dateUntil = pm[self.C_DATE_END]
				if self.C_LOCATION in pm:
					ev.location = self.clean(pm[self.C_LOCATION])
				if self.C_FREQ in pm:
					ev.frequency = pm[self.C_FREQ]
				if self.C_TIME_INTERVAL in pm:
					ev.timeStart = pm[self.C_TIME_INTERVAL][0]
					ev.timeEnd = pm[self.C_TIME_INTERVAL][1]
				if self.C_SPECIAL_NOTE in pm:
					ev.specialEvent = pm[self.C_SPECIAL_NOTE]
				
				if len(pm[self.C_DAY]) > 0:
					for d in pm[self.C_DAY]:
						copied_ev = copy(ev)
						copied_ev.recurrence = d
						if copied_ev.frequency == None:
							copied_ev.frequency = "WEEKLY"
						copied_ev.eventUID = str(self.courseId) + "@" + str(id(copied_ev))
						self.events.append(copied_ev)
				else:
					if self.is_reference:
						ev.eventType = Event.T_REFERENCE
						referenceEvent = ev
					ev.eventUID = str(self.courseId) + "@" + str(id(ev))
					self.events.append(ev)
				
			
			if referenceEvent != None:
				for e in self.events:
					if e.eventType == Event.T_RELATIVE:
						e.dateStart = referenceEvent.dateStart;

		return
	
	def __init__(self, cnr, sem, lang="de"):
		self.is_valid = None
		self.courseId = cnr
		self.events = list()
		
		self.error = None
		
		#private:
		
		self.current_meeting = {}
		self.special_event = ""
		self.date_until = False
		self.is_reference = False
		self.add_meeting = True
		
		params = urllib.urlencode({'lang': lang, 
		                           'semester' : sem,
		                           'lvnr': cnr})
		f = urllib.urlopen("http://online.univie.ac.at/vlvz?%s" % params)
		self.parse_course_information(str(f.read()))
