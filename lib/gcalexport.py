import gflags
import httplib2
import logging
import os
import pprint
import sys

from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.tools import run

class gcal_exporter:
	def __init__(self):
		self.FLAGS = gflags.FLAGS
		self.CLIENT_SECRETS = '/srv/http/univie2gcal_root/lib/client_secrets.json' # todo: better solution
		self.MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to download the client_secrets.json file
and save it at:

   %s

""" % os.path.join(os.path.dirname(__file__), self.CLIENT_SECRETS)
		self.msg = self.CLIENT_SECRETS
		self.FLOW = flow_from_clientsecrets(self.CLIENT_SECRETS,
			scope=[
			  'https://www.googleapis.com/auth/calendar.readonly',
			  'https://www.googleapis.com/auth/calendar',
			],
			message=self.MISSING_CLIENT_SECRETS_MESSAGE)
		gflags.DEFINE_enum('logging_level', 'ERROR',
			['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
			'Set the level of logging detail.')


	def export_to_google_calendar(self, courses):
	  logging.getLogger().setLevel(getattr(logging, self.FLAGS.logging_level))

	  storage = Storage('/tmp/sample.dat')
	  credentials = storage.get()

	  if credentials is None or credentials.invalid:
		credentials = run(self.FLOW, storage)

	  http = httplib2.Http()
	  http = credentials.authorize(http)

	  service = build('calendar', 'v3', http=http)

	  try:

		self.msg = "Success! Now add code here."
	  except AccessTokenRefreshError:
		self.error = "The credentials have been revoked or expired, please re-run the application to re-authorize"
