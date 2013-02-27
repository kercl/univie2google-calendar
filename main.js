
function remove_event(cid, evid) {
	omit = document.getElementById('omit')
	
	if(omit == null)
		return;
	
	glue = "";
	if(omit.value != "" && omit.value != null)
		glue = ",";
	
	omit.value = omit.value + glue + cid + " " + evid;
	
	document.getElementById(cid + " " + evid).className = 'remove'
}

function unhide_events(cid) {
	i = 0;
	
	omit = document.getElementById('omit')
	ev = document.getElementById(cid + " " + i);
	while(ev != null) {
		ev.style.display = 'block'
		ev.className = 'visible'
		
		omit.value = omit.value.replace(cid + " " + i + ",", "");
		omit.value = omit.value.replace(cid + " " + i, "");
		
		i++;
		ev = document.getElementById(cid + " " + i);
	}
}
