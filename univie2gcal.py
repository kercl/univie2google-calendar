#!/usr/bin/env python2
# -*- coding: iso-8859-15

import urllib
import sys
import xml.etree.ElementTree as xml
import string

from apiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow

import httplib2

from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run

FLAGS = gflags.FLAGS

FLOW = OAuth2WebServerFlow(
	client_id='YOUR_CLIENT_ID',
	client_secret='YOUR_CLIENT_SECRET',
	scope='https://www.googleapis.com/auth/calendar',
	user_agent='YOUR_APPLICATION_NAME/YOUR_APPLICATION_VERSION')

C_PARSE_NEW = 0
C_COURSE_NR = 1
C_GCAL_ID = 2
C_SEM = 3
C_LANG = 4

class Course:
	is_valid = None
	
	description = list()
	event = list()
	
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
	
	def parse_meetings(self, txt):
		days = txt.split(';')
		
		print str(days)
		
		for day in days:
			weekly = False
			date_begin = None
			date_end = None
			
			tokens = day.split(" ")
		
		return list()
	
	def parse_course_information(self, page):
		content_groups = self.extract_content(page)
		
		if content_groups == None:
			return
		
		for content in content_groups:
			comment = ""
			event = ""
			lecturer = ""
			termine = list()
			for div in content.iter('div'):
				if 'class' in div.attrib:
					if div.attrib['class'] == 'vlvz_kurzkommentar':
						for text in div.itertext():
							comment = comment + text
					elif div.attrib['class'] == 'vlvz_vortragende':
						for text in div.itertext():
							lecturer = lecturer + text
					elif div.attrib['class'] == 'vlvz_termine':
						termintext = "";
						for text in div.itertext():
							termintext = termintext + text
						termine = self.parse_meetings(termintext)
					elif div.attrib['class'] == 'vlvz_langtitel':
						event = div.find('abbr').text;
						titel_item = div.find('span');
						if 'class' in titel_item.attrib:
							if titel_item.attrib['class'] == 'vlvz_titel':
								event = event + ": " + titel_item.text
			if lecturer != "":
				lecturer = "(" + self.clean(lecturer, encode=True) + ")"
			self.description.append(self.clean(comment, first_alphanum = True) + " " + self.clean(lecturer))
			self.event.append(self.clean(event))

		return
		
	def __init__(self, cnr, sem, lang="de"):
		params = urllib.urlencode({'lang': lang, 
		                           'semester' : sem,
		                           'lvnr': cnr})
		f = urllib.urlopen("http://online.univie.ac.at/vlvz?%s" % params)
		print "\n=======================================================\n"
		self.parse_course_information(f.read())
	
	def __str__(self):
		ret = ""
		for i in range(0, len(self.event)):
			ret = ret + "Event: \t\t" + str(self.event[i]) + "\n"
			# TODO: print all dates
			ret = ret + "Description: \t" + str(self.description[i]) + "\n"
			ret = ret + "\n"
		return ret

def main(argv):
	action = C_PARSE_NEW 
	
	course_number = 0
	gcal_id = ""
	semester = ""
	language = "de"
	
	for arg in argv:
		if action == C_PARSE_NEW:
			if arg in ("-h", "--help"):
				print("University of Vienna course to Google Calender event\n"+
				  "  -h, --help\t Displays this message\n"+
				  "  -c, --course\t Sets the course number, found in the top left corner of a course in the course overview\n"+
				  "  -s, --semester\t Sets the semester (for example S2013 for summer semester 2013)\n"+
				  "  -l, --language\t Language selection (must be de or en)\n"+
				  "  -g, --gcal\t Specifies the google calendar identifier\n")
				exit(0)
			elif arg in ("-c", "--course"):
				action = C_COURSE_NR
			elif arg in ("-g", "--gcal"):
				action = C_GCAL_ID
			elif arg in ("-s", "--semester"):
				action = C_SEM
			elif arg in ("-l", "--language"):
				action = C_LANG
		elif action == C_COURSE_NR:
			try:
				course_number = int(arg)
			except ValueError:
				print("Error: Not a valid course number")
				exit(1)
			action = C_PARSE_NEW
		elif action == C_GCAL_ID:
			gcal_id = arg
			action = C_PARSE_NEW
		elif action == C_SEM:
			semester = arg
			action = C_PARSE_NEW
		elif action == C_LANG:
			language = arg
			action = C_PARSE_NEW
	
	print("Importing " + str(course_number) + " in " + gcal_id);
	if course_number == 0 or gcal_id == "":
		print("Error: No valid course or google calendar specified")
	
	curc = Course(course_number, semester, language)
	
	print str(curc)

if __name__ == "__main__":
   main(sys.argv[1:])
