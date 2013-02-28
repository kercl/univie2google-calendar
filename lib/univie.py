# -*- coding: iso-8859-15

import urllib
import xml.etree.ElementTree as xml
import string
import re
import sys
from copy import copy


DEBUG_MODE = False

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
		self.description = None
		self.location = None
		self.timeStart = None
		self.timeEnd = None
		self.eventUID = None
		self.specialEvent = None
	
	def __eq__(self, ev):
		if self.title == ev.title and self.recurrence == ev.recurrence and \
			self.frequency == ev.frequency and self.dateUntil == ev.dateUntil and \
			self.location == ev.location and self.timeStart == ev.timeStart and\
			self.timeEnd == ev.timeEnd:
			return True
		return False

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

	def to_ical_event(self):
		event = "BEGIN:VEVENT\n"
		if self.dateStart != None and self.timeStart != None and self.timeEnd != None:
			event = event + "DTSTART;TZID=Europe/Vienna:" + self.date_to_str(self.dateStart, True) + "T" + self.time_to_str(self.timeStart, True) + "Z\n"
			event = event + "DTEND;TZID=Europe/Vienna:" + self.date_to_str(self.dateStart, True) + "T" + self.time_to_str(self.timeEnd, True) + "Z\n"
		else:
			return None
		if self.frequency != None and self.recurrence != None:
			event = event + "RRULE:FREQ=" + self.frequency
			if self.dateUntil != None:
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
	
	def to_string(self):
		ret = "Event: \t\t" + self.title + "\n"
		ret = ret + "Date: \t\t" + self.date_to_str(self.dateStart) + "\n"
		ret = ret + "Until: \t\t" + self.date_to_str(self.dateUntil) + "\n"
		ret = ret + "Location: \t" + self.location + "\n"
		ret = ret + "Frequency: \t" + str(self.frequency) + "\n"
		ret = ret + "Recurrence: \t" + str(self.recurrence) + "\n"
		ret = ret + "Time: \t\t" + self.time_to_str(self.timeStart) + " - " + self.time_to_str(self.timeEnd) + "\n"
		ret = ret + u"Description: \t" + self.description + u"\n"
		ret = ret + "\n"
		return ret
		

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
	
	parser_decisions = {-1 : (C_INIT, [0, 14, 20, 18]),
						 0 : (C_DAY, [1,2,11,4,21,0]),
						 1 : (C_FREQ, [3]),
						 2 : (C_DATE, [4, 15, 19, 6, 17, 2, 0]),
						 3 : ("von", [2]),
						 4 : (C_TIME_INTERVAL, [9, 10]),
						 6 : ("bis", [2]),
						 9 : ("Ort:", [10]),
						 10: (C_LOCATION, [C_END]),
						 11: ("jeweils", [12,4]),
						 12: ("von", [4]),
						 14: ("Vorbesprechung", [2, 16, 17]),
						 15: (C_TIME, [2, 10]),
						 16: (C_IGNORE_UNTIL_DAY, [C_END]),
						 17: ("und", [18, 2]),
						 18: ("Beginn:", [2,16]),
						 19: ("um", [15]),
						 20: ("Voraussichtlich", [0]),
						 21: ("und", [0]),
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
		page = page.replace("&uuml;", "ü")
		page = page.replace("&auml;", "ä")
		page = page.replace("&ouml;", "ö")
		page = page.replace("&Uuml;", "Ü")
		page = page.replace("&Auml;", "Ä")
		page = page.replace("&Ouml;", "Ö")
		
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
	
	def parse_hh_mm(self, txt):
		txt = txt.replace(',', '')
		m = re.split('[.:]', txt)
		try:
			if len(m) == 2 or (len(m)==3 and m[2] == ''):
				return {"hour" : int(m[0]), "minute" : int(m[1])}
		except ValueError:
			return None
	
	def parse_time_interval(self, txt):
		txt = txt.replace(',', '')
		s = txt.split('-')
		if len(s) == 2:
			d1 = self.parse_hh_mm(s[0])
			d2 = self.parse_hh_mm(s[1])
			if d1 != None and d2 != None:
				timeinterval = [d1, d2]
				return timeinterval
			return None
		return None
	
	def match(self, tokens, idx, mtype):
		txt = tokens[idx]
		
		if mtype == self.C_DATE:
			txt = txt.replace(',', '')
			m = txt.split('.')
			if len(m) == 3 or (len(m)==4 and m[3] == ''):
				try:
					date = {"day" : int(m[0]), "month" : int(m[1]), "year" : int(m[2])}
					if date['year'] < 1000:
						date['year'] = 2000 + date['year']
				except ValueError:
					return None
				return date
			return None
		elif mtype == self.C_TIME_INTERVAL:
			tint = self.parse_time_interval(txt)
			if tint == None:
				try:
					tint = self.parse_time_interval(tokens[idx] + tokens[idx+1] + tokens[idx+2])
					if tint != None:
						self.jump_increment = 3
					return tint
				except Exception:
					return None
			return tint
		elif mtype == self.C_TIME:
			hhmm = self.parse_hh_mm(txt)
			if hhmm == None:
				if txt.isdigit():
					h = int(txt)
					try:
						academic = tokens[idx:idx+3]
						if 'Uhr' in academic and ('s.t.' in academic or 'c.t.' in academic):
							if 'c.t.' in academic:
								m = 15
							else:
								m = 0
							self.jump_increment = 3
							return {"hour": h, "minute": m}
						else:
							return None
					except Exception:
						return None
			return hhmm
		elif mtype == self.C_DAY:
			txt = txt.replace(',', '')
			days = ["MO", "DI", "MI", "DO", "FR", "SA", "SO", "Mo", "Di", "Mi", "Do", "Fr", "Sa", "So", "Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
			if txt in days:
				return ["MO", "TU", "WE", "TH", "FR", "SA", "SO", "MO", "TU", "WE", "TH", "FR", "SA", "SO", "MO", "TU", "WE", "TH", "FR", "SA", "SO"][days.index(txt)]
		elif mtype == self.C_FREQ:
			if txt in ("wtl", u"wöchtentlich"):
				return "WEEKLY"
			if txt in ("14-tg"):
				return "WEEKLY2"
		elif type(mtype) is str:
			return txt[:len(mtype)] == mtype
		return None
		
	def is_preposition(self, txt):
		return txt in ["im", "in", "am"]
	
	def extend_time(self, tm, l=120):
		return [tm, {'minute': tm['minute']+l % 60, 'hour': tm['hour']+l / 60}]

	def rec_parse(self, tokens, it, state_id):
		state = self.parser_decisions[state_id]
		
		if it == len(tokens) or state[0] == self.C_END:
			if DEBUG_MODE:
				print "   [PARSER FINISHED]" #DBG
			return it
		
		if state[0] == self.C_INIT:
			it = it - 1
			if DEBUG_MODE:
				print "ENTERING STATE: " + str(state_id) + " => " + str(state) + " (it="+str(it)+")" #DBG
		elif state[0] == self.C_IGNORE_UNTIL_DAY:
			if DEBUG_MODE:
				print "ENTERING STATE: " + str(state_id) + " => " + str(state) + " (it="+str(it)+")" #DBG
			self.add_meeting = False
			while self.match(tokens, it, self.C_DAY) == None:
				it = it + 1
			if DEBUG_MODE:
				print "IGNORE TO " + str(it) #DBG
			return it
		else:
			t = tokens[it]
			
			if DEBUG_MODE:
				print "ENTERING STATE: " + str(state_id) + " => " + str(state) + " - TOKEN{" + t + "}" + " (it="+str(it)+")" #DBG
			
			self.jump_increment = 1
			m = self.match(tokens, it, state[0])
		
			if DEBUG_MODE:
				print("   [MATCH RESULT] " + str(m))
			if m == None or m == False:
				if state[0] == self.C_LOCATION:
					if self.match(tokens, it, "Beginn:"):
						return self.rec_parse(tokens, it, self.C_END);
					
					if it > 0:
						if self.is_preposition(tokens[it-1]) == False:
							if self.match(tokens, it, self.C_DAY) != None:
								return self.rec_parse(tokens, it, self.C_END);
					else:
						if self.match(tokens, it, self.C_DAY) != None:
								return self.rec_parse(tokens, it, self.C_END);
					if self.is_preposition(t) == False or self.current_meeting[self.C_LOCATION] != "":
						self.current_meeting[self.C_LOCATION] = self.current_meeting[self.C_LOCATION] + " " + t
					return self.rec_parse(tokens, it + self.jump_increment, state_id)
				else:
					if DEBUG_MODE:
						print "   [STATE INVALID]" #DBG
					return False
			else:
				if state[0] == self.C_DATE:
					if self.date_until == False:
						self.current_meeting[self.C_DATE_BEG].append(m)
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
				elif t[:14] == 'Vorbesprechung':
					omit_words = ['und', 'erster', 'Termin', 'am', 'um']
					while tokens[it + self.jump_increment] in omit_words:
						self.jump_increment = self.jump_increment + 1
					self.is_reference = True
					self.current_meeting[self.C_SPECIAL_NOTE] = t
		
		cur_increment = self.jump_increment
		for s in state[1]:
			r = self.rec_parse(tokens, it + cur_increment, s)
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
			self.current_meeting[self.C_DATE_BEG] = []
			self.add_meeting = True
			nexti = self.rec_parse(tokens, nexti, -1)
			
			if self.add_meeting:
				parsed_meeting.append(self.current_meeting)
			
			if nexti == None:
				if DEBUG_MODE:
					print "   [PARSER ABORTED | SOME TOKENS REMAIN UNPARSED]" #DBG
				break

		return parsed_meeting

			
	def meetings_empty(self, pm):
		if len(pm) <= 2:
			#if pm[self.C_LOCATION] == "" and pm[self.C_DATE_BEG] == []:
				return True
		return False
	
	def append_event_once(self, ev):
		for e in self.events:
			if ev == e:
				return
		self.events.append(ev)
	
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
				if len(pm[self.C_DATE_BEG]) == 0:
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
				
				if len(pm[self.C_DAY]) > 1:
					for d in pm[self.C_DAY]:
						copied_ev = copy(ev)
						copied_ev.recurrence = d
						if copied_ev.frequency == None:
							copied_ev.frequency = "WEEKLY"
						if ev.eventType != Event.T_RELATIVE:
							copied_ev.dateStart = (pm[self.C_DATE_BEG])[0]
						copied_ev.eventUID = str(self.courseId) + "@" + str(id(copied_ev))
						self.append_event_once(copied_ev)
				else:
					if len(pm[self.C_DAY]) > 0:
						ev.recurrence = (pm[self.C_DAY])[0]
						if ev.frequency == None:
							ev.frequency = "WEEKLY"
					if len(pm[self.C_DATE_BEG]) > 1:
						for d in pm[self.C_DATE_BEG]:
							copied_ev = copy(ev)
							copied_ev.dateStart = d
							copied_ev.eventUID = str(self.courseId) + "@" + str(id(copied_ev))
							self.append_event_once(copied_ev)
					else:
						if len(pm[self.C_DATE_BEG]) > 0:
							ev.dateStart = (pm[self.C_DATE_BEG])[0]
						if self.is_reference:
							ev.eventType = Event.T_REFERENCE
							referenceEvent = ev
						ev.eventUID = str(self.courseId) + "@" + str(id(ev))
						self.append_event_once(ev)
				
			
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
		self.jump_increment = 1
		
		params = urllib.urlencode({'lang': lang, 
		                           'semester' : sem,
		                           'lvnr': cnr})
		f = urllib.urlopen("http://online.univie.ac.at/vlvz?%s" % params)
		self.parse_course_information(str(f.read()))
