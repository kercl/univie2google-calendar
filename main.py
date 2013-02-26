#-*- coding: utf-8 -*-

import cgi
import cgitb
import univie
import layout
import datetime

def get_list_semesters():
	prefix = ["S", "W"]
	long_prefix = ["summer semester ", "winter semester "]
	curmonth = int(datetime.datetime.now().strftime("%m"))
	
	if curmonth >= 2 and curmonth < 7:
		pi = 0
	else:
		pi = 1
	
	lst = []
	year = int(datetime.datetime.now().strftime("%Y"))
	for i in range(0,5):
		key = (prefix[pi] + str(year))
		value = (long_prefix[pi] + str(year))
		lst.append((key, value))
		if pi == 0:
			year = year - 1
		pi = (pi - 1) % 2
	
	return lst
			

def univie2gcal_app(env, start_response):
	import cgitb
	output = ""
	
	form = cgi.FieldStorage(fp=env['wsgi.input'], environ=env)

	lastError = ""
	
	new = ""
	
	if 'courses' in form:
		course_numbers = form['courses'].value.split(',')
	else:
		course_numbers = []
	try:
		if 'inp_cnr' in form:
			int(form['inp_cnr'].value)
			new = form['inp_cnr'].value
			course_numbers.insert(0, str(form['inp_cnr'].value))
	except ValueError:
		lastError = "<div class='error'>&#9888; Error: course number must be an integer</div>"
	
	existing_course_numbers = []
	courses = []
	for cnr in course_numbers:
		c = univie.Course(str(cnr), "S2013")
		if c.error == None:
			existing_course_numbers.append(cnr)
			courses.append(c)
		else:
			lastError = "<div class='error'>&#9888; Error: " + c.error + "</div>"

	output = output + \
"""<!doctype html>
<html>
	<head>
		<link rel='stylesheet' type='text/css' href='/univie2gcal_root/css/main.css' />
		<title>univie2google-calendar</title>
	</head>
	<body>
		<div class='content'>
			<h1>Import univie-course into Google calendar:</h1>""" + lastError + """
			<form method='get' action=''>Select course: <select name='sem'>"""
	selected = " selected='selected'"
	for s in get_list_semesters():
		output = output + "<option"+ selected +">"+ s[1] +"</option>"
		selected = ""
	output = output + """</select><input type='hidden' name='courses' value='""" + (','.join(existing_course_numbers)) + """' />
				<input type='text' name='inp_cnr' /><input type='submit' value='Add course' />
			</form><br />"""
	first = True
	
	for c in courses:
		output = output + layout.html_format_course(c, new=(new == c.courseId and first))
		first = False

	output = output +\
"""		</div>
	</body>
</html>"""

	status = '200 OK'
	headers = [('Content-type', 'text/html'),
				('Content-Length', str(len(output)))]
	start_response(status, headers)

	yield output

application = univie2gcal_app
