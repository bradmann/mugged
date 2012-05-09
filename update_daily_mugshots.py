import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mugged.settings")
from muggedapp.api import mugapi
import logging

if __name__ == '__main__':
	logging.basicConfig(filename='/var/log/muggedapp/daily_mugshot_scrapes.log', level=logging.INFO, format='%(asctime)s %(message)s')
	logging.info('Starting daily mugshot scrape.')
	uris = mugapi.update_daily_mugshots()
	logging.info('Daily mugshot scrape completed. The URIs collected are:')
	for uri in uris:
		logging.info(uri)
