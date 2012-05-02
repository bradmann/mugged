from muggedapp.models import FacebookUser, MugshotSearch, MugshotSearchResult
from django.utils import timezone

import datetime
import requests
import re

base_uri = 'http://florida.arrests.org/search.php'
	
def get_birthdate(birthday):
	if not birthday or len(birthday.split('/')) != 3:
		return None
	month, day, year = birthday.split('/')
	return datetime.date(int(year), int(month), int(day))
	
def verify(id, mugshot):
	mugshot = MugshotSearchResult.objects.filter(search__fbuser__fbid=id).get(arrestpath=mugshot)
	mugshot.matches_user = True
	mugshot.save()
	
def reject(id, mugshot):
	mugshot = MugshotSearchResult.objects.filter(search__fbuser__fbid=id).get(arrestpath=mugshot)
	mugshot.matches_user = False
	mugshot.save()

def reject_all(id):
	mugshots = MugshotSearchResult.objects.filter(search__fbuser__fbid=id, matches_user=None)
	mugshots.update(matches_user=False)
	
def verify_all(id):
	mugshots = MugshotSearchResult.objects.filter(search__fbuser__fbid=id, matches_user=None)
	mugshots.update(matches_user=True)

def search_and_update(fbuser):
	id = fbuser['id']
	fname = fbuser.get('first_name')
	mname = fbuser.get('middle_name')
	lname = fbuser.get('last_name')
	birthday = fbuser.get('birthday')
	birthdate = get_birthdate(birthday)
	gender = {'male': 'M', 'female': 'F'}.get(fbuser.get('gender'))
	
	dbUser, created = FacebookUser.objects.get_or_create(fbid=id)

	dbSearch = MugshotSearch.objects.filter(fbuser=dbUser, fname=fname, mname=mname, lname=lname, birthdate=birthdate, gender=gender)
	if dbSearch.count() == 0:
		MugshotSearch.objects.create(fbuser=dbUser, fname=fname, mname=mname, lname=lname, birthdate=birthdate, gender=gender)
	dbSearch = MugshotSearch.objects.filter(fbuser=dbUser)
	for search in dbSearch:
		if search.last_searched < (timezone.now() - datetime.timedelta(1)):
			search.last_searched=timezone.now()
			search.save()
			for request_params in search.search_requests():
				results = search_mugshot_web(request_params)
				for result in results:
					MugshotSearchResult.objects.create(search=search, thumbpath=result['thumbpath'], arrestpath=result['arrestpath'])
	
	return MugshotSearchResult.objects.filter(search__fbuser=dbUser).exclude(matches_user=False).values()	

def search_mugshot_web(request_params):
	req = requests.get(base_uri, params=request_params)
	page = req.content
	imgpaths = re.findall("<img src='(/thumbs/[^']*)'", page)
	arrestpaths = re.findall("<a href='(/Arrests/[^']*)'", page)
	if len(imgpaths) == 0:
		return []
	paths = [{'thumbpath': imgpaths[i], 'arrestpath': arrestpaths[i], 'matches_user': None} for i in xrange(len(imgpaths))]
	pagenum = 1
	patharr = paths[:]
	while len(paths) == 42:
		request_params['page'] = pagenum
		req = requests.get(base_uri, params=request_params)
		page = req.content
		imgpaths = re.findall("<img src='(/thumbs/[^']*)'", page)
		arrestpaths = re.findall("<a href='(/Arrests/[^']*)'", page)
		paths = [{'thumbpath': imgpaths[i], 'arrestpath': arrestpaths[i], 'matches_user': None} for i in xrange(len(imgpaths))]
		patharr.extend(paths)
		pagenum += 1
	return patharr