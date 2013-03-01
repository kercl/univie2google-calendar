#-*- coding: utf-8 -*-

import cgi
import cgitb
import lib.univie as univie
import lib.gcalexport as gcalexport
import layout
import datetime

PROJECT_ROOT = '/univie2gcal_root'

def get_list_semesters():
	prefix = ["S", "W"]
	long_prefix = ["S", "W"]
	curmonth = int(datetime.datetime.now().strftime("%m"))
	
	if curmonth >= 2 and curmonth < 7:
		pi = 0
	else:
		pi = 1
	
	lst = []
	year = int(datetime.datetime.now().strftime("%Y"))
	for i in range(0,5):
		lst.append(prefix[pi] + str(year))
		if pi == 0:
			year = year - 1
		pi = (pi - 1) % 2
	
	return lst

def get_cgi_variable(form, name, default=None):
	if name in form:
		return form[name].value
	else:
		return default

def gcal(env, form):
	exp = gcalexport.gcal_exporter()
	output = "Hallo: " + exp.msg
	exp.export_to_google_calendar(None)
	
	page = {'status': '200 OK',
			'header': [('Content-type', 'text/html'), ('Content-Length', str(len(output)))],
			'content': output}
	return page

def ical(env, form):
	output = """BEGIN:VCALENDAR
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
END:VTIMEZONE\n"""
	
	sem = get_cgi_variable(form, 'sem', (get_list_semesters()[0])[0])
	if 'courses' in form:
		course_numbers = form['courses'].value.split(',')
	else:
		course_numbers = []
	
	omit = []
	if 'omit' in form:
		omit = form['omit'].value.split(',')
	else:
		omit = []

	for cnr in course_numbers:
		c = univie.Course(str(cnr), sem)
		i = 0
		if c.error == None:
			for e in c.events:
				if layout.event_omitted(cnr, i, omit):
					i = i + 1
					continue
				output = output + e.to_ical_event().encode('utf-8') + "\n"
				i = i + 1

	output = output + "END:VCALENDAR"
	
	page = {'status': '200 OK',
			'header': [('Content-type', 'text/calendar'), ('Content-Length', str(len(output))), ('Content-Disposition', 'attachment; filename=mycalendar.ics;')],
			'content': output}
	return page

def main(env, form):
	output = ""
	
	lastError = ""
	new = ""
	
	sem = get_cgi_variable(form, 'sem', (get_list_semesters()[0])[0])
	if 'courses' in form:
		course_numbers = form['courses'].value.split(',')
	else:
		course_numbers = []
	
	omit = []
	if 'omit' in form:
		omit = form['omit'].value.split(',')
	else:
		omit = []
	
	try:
		if 'inp_cnr' in form:
			int(form['inp_cnr'].value)
			new = form['inp_cnr'].value
			if new in course_numbers:
				new = ""
			else:
				course_numbers.insert(0, str(form['inp_cnr'].value))
	except ValueError:
		lastError = "<div class='error'>&#9888; Error: course number must be an integer</div>"
	
	existing_course_numbers = []
	courses = []
	for cnr in course_numbers:
		c = univie.Course(str(cnr), sem)
		if c.error == None:
			existing_course_numbers.append(cnr)
			courses.append(c)
		else:
			lastError = "<div class='error'>&#9888; Error: " + c.error + "</div>"

	output = output + \
"""<!doctype html>
<html>
	<head>
		<link rel='stylesheet' type='text/css' media='all' href='""" + PROJECT_ROOT + """/css/main.css' />
		<link rel='stylesheet' type='text/css' media='handheld' href='""" + PROJECT_ROOT + """/css/mobile.css' />  
		<script type="text/javascript" src='""" + PROJECT_ROOT + """/main.js'></script>
		<title>univie2google-calendar</title>
	</head>
	<body>
		<div class='content'>
			<h1>Import univie-course:</h1>""" + lastError + """
			<form id='main_form' method='post' action='""" + env['SCRIPT_NAME'] + """/'>Select course: """
	if len(existing_course_numbers) == 0:
		output = output + """<select name='sem'>"""
		selected = " selected='selected'"
		for s in get_list_semesters():
			output = output + "<option"+ selected +" value='" + s + "'>"+ s +"</option>"
			selected = ""
		output = output + "</select>"
	else:
		output = output + sem + """<input type='hidden' name='sem' value='""" + sem + """' />"""
	output = output + """<input type='hidden' id='omit' name='omit' value='""" + (','.join(omit)) + """' />
			<input type='hidden' name='courses' value='""" + (','.join(existing_course_numbers)) + """' />
				<input type='text' name='inp_cnr' />&nbsp;<input type='submit' name='dir' value='Add course' />&nbsp;
				<input type='submit' name='dir' value='Download iCal' />&nbsp;
				<input type='button' value='Dismiss' onclick='window.location.href=\"""" + env['SCRIPT_NAME'] + """/\"' />
			</form><br />""" # TODO: Insert <input type='submit' name='dir' value='To Google calendar' />&nbsp;
	first = True

	for c in courses:
		output = output + layout.html_format_course(c, new=(new == c.courseId and first), omit=omit)
		first = False

	output = output +\
"""		</div></body>
</html>"""

	page = {'status': '200 OK',
			'header': [('Content-type', 'text/html'), ('Content-Length', str(len(output)))],
			'content': output}
	
	return page


def univie2gcal_app(env, start_response):
	form = cgi.FieldStorage(fp=env['wsgi.input'], environ=env)
	
	if get_cgi_variable(form, 'dir') == 'Download iCal':
		page = ical(env, form)
	elif get_cgi_variable(form, 'dir') == 'To Google calendar':
		page = gcal(env, form)
	else:
		page = main(env, form)

	start_response(page['status'], page['header'])
	
	yield page['content']

application = univie2gcal_app
