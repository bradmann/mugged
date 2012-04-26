from django.http import HttpResponse
from django.http import HttpRequest
from django.shortcuts import render_to_response
from django.conf import settings
import json
import hmac
import hashlib
import requests
import re
import datetime
from base64 import urlsafe_b64decode, urlsafe_b64encode

import fbapi

base_uri = 'http://florida.arrests.org/search.php'

def index(request):
	if request.method == 'POST':
		access_token = fbapi.get_token(request.POST.get('signed_request'))
		request.session['access_token'] = access_token
		if access_token:
			friends = fbapi.fb_call('me/friends', args={'access_token': access_token})
			friendarr = friends['data']
			while friends.has_key('paging') and friends['paging'].has_key('next'):
				next_url = friends['paging']['next']
				r = requests.get(next_url, params={'access_token': access_token})
				friends = json.loads(r.content)
				friendarr.extend(friends['data'])
			friendstring = json.dumps(friendarr)
			return render_to_response('index.html', {'friends': friendstring, 'friendarr': friendarr})
		else:
			return fbapi.oauth_redirect()
	else:
		return HttpResponse('This page only supports POSTS')
		
def get_age(birthday):
	month, day, year = birthday.split('/')
	birthdate = datetime.date(year, month, day)
	delta = datetime.datetime.now - birthdate
	return int(delta.days / 365.25)
		
def mugshot(request, id):
	access_token = request.session.get('access_token')
	fbuser = fbapi.fb_call(str(id), args={'access_token': access_token})
	first_name = fbuser['first_name']
	last_name = fbuser['last_name']
	birthday = fbuser.get('birthday', None)
	gender = fbuser.get('gender', None)
	request_params = {'fname': first_name, 'lname': last_name, 'fpartial': 'True'}
	if gender == 'male':
		request_params['sex'] = 'M'
	elif gender == 'female':
		request_params['sex'] = 'F'
	if birthday and len(birthday.split('/')) == 3:
		age = get_age(birthday)
		request_params['minage'] = age
		request_params['maxage'] = age
	req = requests.get(base_uri, params=request_params)
	page = req.content
	paths = re.findall("<img src='(/thumbs/[^']*)'", page)
	if len(paths) == 0:
		return HttpResponse('', status=204)
	pagenum = 1
	patharr = paths[:]
	while len(paths) == 42:
		request_params['page'] = pagenum
		req = requests.get(base_uri, params=request_params)
		page = req.content
		paths = re.findall("<img src='(/thumbs/[^']*)'", page)
		patharr.extend(paths)
		pagenum += 1
	return render_to_response('mugshot.html', {'name': fbuser['name'], 'id': str(id), 'patharr': patharr, 'birthday': birthday})