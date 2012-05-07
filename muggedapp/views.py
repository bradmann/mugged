from django.http import HttpResponse
from django.http import HttpRequest
from django.views.decorators.http import require_http_methods
from django.shortcuts import render_to_response
from django.conf import settings
import json

from api import fbapi, mugapi

@require_http_methods(['GET', 'POST'])
def index(request):
	friendarr = fbapi.get_friends(request)
	friendstring = json.dumps(friendarr)
	return render_to_response('index.html', {'friends': friendstring, 'friendarr': friendarr})
		
@require_http_methods(['GET', 'POST'])
def mugshot(request, id):
	if request.method == 'GET':
		fbuser = fbapi.get_user(request, id)
		patharr = mugapi.search_and_update(fbuser)
		if not patharr:
			return HttpResponse('', status=204)
		return render_to_response('mugshot.html', {'name': fbuser['name'], 'id': str(id), 'patharr': patharr})
	else:
		post = json.loads(request.raw_post_data)
		if post['action'] == 'verify_mugshot':
			mugapi.verify(id, post['arrest'])
		elif post['action'] == 'reject_mugshot':
			mugapi.reject(id, post['arrest'])
		elif post['action'] == 'verify_all':
			mugapi.verify_all(id)
		elif post['action'] == 'reject_all':
			mugapi.reject_all(id)
		return HttpResponse('', status=204)

@require_http_methods(['GET'])
def login(request):
	return HttpResponse('This is the login page again.')