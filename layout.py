#-*- coding: utf-8 -*-

import lib.univie as univie

def event_omitted(cid, i, omit):
	for o in omit:
		l = o.split()
		try:
			if int(cid) == int(l[0]) and int(i) == int(l[1]):
				return True
		except Exception:
			pass
	return False

def html_format_course(course, new=False, omit=[]):
	fade = ''
	if new:
		fade = ' fade'
	output = "<div class='course" + fade + "'><h2><span class='button_close' onclick='unhide_events(" + str(course.courseId) + ")'>&#8634;</span>&nbsp;Course: " + str(course.courseId) + "</h2>"
	
	dayOfWeek = {'MO':'monday', 'TU':'tuesday', 'WE':'wednesday', 'TH':'thursday', 'FR':'friday', 'SA':'saturday', 'SO':'sonday'}
	i = 0
	for e in course.events:
		hiddenstyle = ""
		if event_omitted(course.courseId, i, omit):
			hiddenstyle = "style='display:none'"
		
		special = ""
		if e.specialEvent != None:
			special = e.specialEvent + " "
		title = "<h3>" + (special + e.title).encode('iso-8859-15') + "</h3>"
		if e.recurrence != None and e.frequency != None:
			dateTime = "every " + dayOfWeek[e.recurrence] + ", "
		else:
			dateTime = ""
		if e.dateUntil == None:
			dateTime = dateTime + e.date_to_str(e.dateStart) + " "
		else:
			dateTime = dateTime + e.date_to_str(e.dateStart) + " until " + e.date_to_str(e.dateUntil)
		dateTime = dateTime + " from " + e.time_to_str(e.timeStart) + " to " + e.time_to_str(e.timeEnd)
		location = "<tr><td valign='top' align='left'><b style='font-size:10pt'>Location: </b></td><td>" + e.location.encode('iso-8859-15') + "</td></tr>"
		description = "<tr><td valign='top' align='left'><b>Description: </b></td><td> " + e.description.encode('iso-8859-15') + "</td></tr>"
		
		output = output + \
"""<div id='""" + str(course.courseId) + " " + str(i) + """' class='event' """ + hiddenstyle + """><div class='course_head'>
		<span class='button_close' onclick='remove_event(""" + str(course.courseId) + "," + str(i) + """)'>&#10799;</span>
	</div>""" + title + "<br />" + dateTime + "<br /><table>" + location + description + """</table></div>"""

		i = i + 1
		
	output = output + "</div>"
	
	return output
