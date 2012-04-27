import datetime
import requests
import re

base_uri = 'http://florida.arrests.org/search.php'

def get_age(birthday):
	month, day, year = birthday.split('/')
	birthdate = datetime.datetime(int(year), int(month), int(day))
	delta = datetime.datetime.now() - birthdate
	return int(delta.days / 365.25)

def run_search(request, fbuser):
	first_name = fbuser['first_name']
	last_name = fbuser['last_name']
	birthday = fbuser.get('birthday', None)
	gender = fbuser.get('gender', None)
	request_params = {'fname': first_name, 'lname': last_name, 'fpartial': 'True'}
	gender_map = {'male': 'M', 'female': 'F'}
	request_params['sex'] = gender_map.get(gender, 'M')
	if birthday and len(birthday.split('/')) == 3:
		age = get_age(birthday)
		request_params.update({'minage': age, 'maxage': age})
	req = requests.get(base_uri, params=request_params)
	page = req.content
	paths = re.findall("<img src='(/thumbs/[^']*)'", page)
	if len(paths) == 0:
		return None
	pagenum = 1
	patharr = paths[:]
	while len(paths) == 42:
		request_params['page'] = pagenum
		req = requests.get(base_uri, params=request_params)
		page = req.content
		paths = re.findall("<img src='(/thumbs/[^']*)'", page)
		patharr.extend(paths)
		pagenum += 1
	return patharr