from muggedapp.models import FacebookUser, MugshotSearch, MugshotSearchResult
from django.utils import timezone

import datetime
import requests
import re

base_uri = 'http://florida.arrests.org/search.php'

def get_age(birthday):
	month, day, year = birthday.split('/')
	birthdate = datetime.datetime(int(year), int(month), int(day))
	delta = datetime.datetime.now() - birthdate
	return int(delta.days / 365.25)
	
def get_birthdate(birthday):
	if not birthday or len(birthday.split('/')) != 3:
		return None
	month, day, year = birthday.split('/')
	birthdate = datetime.date(int(year), int(month), int(day))
	
def verify(id, mugshot):
	mugshot = MugshotSearchResult.objects.filter(search__fbuser__fbid=id).get(arrestpath=mugshot)
	mugshot.matches_user = True
	mugshot.save()
	
def reject(id, mugshot):
	mugshot = MugshotSearchResult.objects.filter(search__fbuser__fbid=id).get(arrestpath=mugshot)
	mugshot.matches_user = False
	mugshot.save()
		

def search_and_update(fbuser):
	id = fbuser['id']
	first_name = fbuser['first_name']
	last_name = fbuser['last_name']
	birthday = fbuser.get('birthday', None)
	birthdate = get_birthdate(birthday)
	gender_map = {'male': 'M', 'female': 'F'}
	gender = gender_map.get(fbuser.get('gender', None), None)
	try:
		dbUser = FacebookUser.objects.get(fbid=id)
	except:
		dbUser = FacebookUser(fbid=id)
		dbUser.save()
	try:
		dbSearch = MugshotSearch.objects.get(fbuser=dbUser.fbid)
	except:
		dbSearch = MugshotSearch(fbuser=dbUser, fname=first_name, lname=last_name, birthdate=birthdate, gender=gender, last_searched=timezone.now())
		dbSearch.save()
		results = search_mugshot_web(first_name, last_name, gender, birthday)
		if not results: return None
		for result in results:
			dbResult = MugshotSearchResult(thumbpath=result['thumbpath'], arrestpath=result['arrestpath'], search=dbSearch)
			dbResult.save()
		return results
	if dbSearch.last_searched > (timezone.now() - datetime.timedelta(1)):
		dbResults = MugshotSearchResult.objects.filter(search=dbSearch).exclude(matches_user=False)
		return [res for res in dbResults.iterator()]
	else:
		last_searched = dbSearch.last_searched
		dbSearch.last_searched = timezone.now()
		dbSearch.save()
		results = search_mugshot_web(first_name, last_name, gender, birthday, last_searched)
		if not results: return None
		for result in results:
			dbResult = MugshotSearchResult(thumbpath=result['thumbpath'], arrestpath=result['arrestpath'], search=dbSearch)
			dbResult.save()
		return results

def search_mugshot_web(first_name, last_name, gender, birthday=None, arrested_after=None):
	request_params = {'fname': first_name, 'lname': last_name, 'fpartial': 'True'}
	if birthday: request_params.update({'sex': gender})
	if birthday and len(birthday.split('/')) == 3:
		age = get_age(birthday)
		request_params.update({'minage': age, 'maxage': age})
	if arrested_after:
		request_params.update({'startdate': arrested_after.strf_time('%m%%2F%d%%2F%Y'), 'enddate': datetime.datetime.now().strftime('%m%%2F%d%%2F%Y')})
	req = requests.get(base_uri, params=request_params)
	page = req.content
	imgpaths = re.findall("<img src='(/thumbs/[^']*)'", page)
	arrestpaths = re.findall("<a href='(/Arrests/[^']*)'", page)
	if len(imgpaths) == 0:
		return None
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