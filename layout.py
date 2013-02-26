#-*- coding: utf-8 -*-

import univie

def html_format_course(course, new=False, remove_button = True):
	fade = ''
	if new:
		fade = ' fade'
	output = "<div class='course" + fade + "'><h2>Course: " + str(course.courseId) + "</h2>"
	
	dayOfWeek = {'MO':'monday', 'TU':'tuesday', 'WE':'wednesday', 'TH':'thursday', 'FR':'friday', 'SA':'saturday', 'SO':'sonday'}
	for e in course.events:
		special = ""
		if e.specialEvent != None:
			special = e.specialEvent + " "
		title = "<h3>" + (special + e.title).encode('iso-8859-15') + "</h3>"
		if e.recurrence != None:
			dateTime = "every " + dayOfWeek[e.recurrence] + ", "
		else:
			dateTime = ""
		if e.dateUntil == None:
			dateTime = dateTime + "starting on " + e.date_to_str(e.dateStart) + " "
		else:
			dateTime = dateTime + e.date_to_str(e.dateStart) + " until " + e.date_to_str(e.dateUntil)
		dateTime = dateTime + " from " + e.time_to_str(e.timeStart) + " to " + e.time_to_str(e.timeEnd)
		location = "<tr><td valign='top' align='left'><b>Location: </b></td><td>" + e.location.encode('iso-8859-15') + "</td></tr>"
		description = "<tr><td valign='top' align='left'><b>Description: </b></td><td> " + e.description.encode('iso-8859-15') + "</td></tr>"
		
		output = output + \
"""<div class='event'><div class='course_head'>
		<input type='button' value='&#10799;' class='close' />
	</div>""" + title + "<br />" + dateTime + "<br /><table style='text-size:10pt'>" + location + description + """</table></div>"""
		
	output = output + "</div>"
	
	return output
