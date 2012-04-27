from django.http import HttpResponse
from django.http import HttpRequest
from django.views.decorators.http import require_http_methods
from django.shortcuts import render_to_response
from django.conf import settings
import json

from api import fbapi, mugapi

@require_http_methods(['POST'])
def index(request):
	friendarr = fbapi.get_friends(request)
	friendstring = json.dumps(friendarr)
	return render_to_response('index.html', {'friends': friendstring, 'friendarr': friendarr})
		
def mugshot(request, id):
	fbuser = fbapi.get_user(request, id)
	patharr = mugapi.run_search(request, fbuser)
	if not patharr:
		return HttpResponse('', status=204)
	return render_to_response('mugshot.html', {'name': fbuser['name'], 'id': str(id), 'patharr': patharr})