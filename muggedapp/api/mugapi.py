from muggedapp.models import FacebookUser, MugshotSearch, MugshotSearchResult

import datetime
import requests
import re

base_uri = 'http://florida.arrests.org/search.php'

def get_age(birthday):
	month, day, year = birthday.split('/')
	birthdate = datetime.datetime(int(year), int(month), int(day))
	delta = datetime.datetime.now() - birthdate
	return int(delta.days / 365.25)

def check_db(id):
	dbUser = FacebookUser.objects.get(fbid=id)
	if dbUser:
		dbSearch = MugshotSearch.objects.get(fbuser=dbUser.fbid)
		if dbSearch.last_searched > (datetime.datetime.now() - datetime.timedelta(1)):
			dbResults = MugshotSearchResult.object.filter(search=dbSearch.id)
			return [(imgpath, arrestpath) for imgpath, arrestpath in dbResults]
		else:
			return None

def scrape_mugshot(first_name, last_name, birthday, gender):
	request_params = {'fname': first_name, 'lname': last_name, 'fpartial': 'True', 'sex': gender}
	if birthday and len(birthday.split('/')) == 3:
		age = get_age(birthday)
		request_params.update({'minage': age, 'maxage': age})
	req = requests.get(base_uri, params=request_params)
	page = req.content
	imgpaths = re.findall("<img src='(/thumbs/[^']*)'", page)
	arrestpaths = re.findall("<a href='(/Arrests/[^']*)'", page)
	if len(imgpaths) == 0:
		return None
	paths = zip(imgpaths, arrestpaths)
	pagenum = 1
	patharr = paths[:]
	while len(paths) == 42:
		request_params['page'] = pagenum
		req = requests.get(base_uri, params=request_params)
		page = req.content
		imgpaths = re.findall("<img src='(/thumbs/[^']*)'", page)
		arrestpaths = re.findall("<a href='(/Arrests/[^']*)'", page)
		paths = zip(imgpaths, arrestpaths)
		patharr.extend(paths)
		pagenum += 1
	return patharr
			
def run_search(request, fbuser):
	id = fbuser['id']
	first_name = fbuser['first_name']
	last_name = fbuser['last_name']
	birthday = fbuser.get('birthday', None)
	gender_map = {'male': 'M', 'female': 'F'}
	gender = gender_map.get(fbuser.get('gender', None), None)
	results = check_db(id)
	if results:
		return results
	return scrape_mugshot(first_name, last_name, birthday, gender)