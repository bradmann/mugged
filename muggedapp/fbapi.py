from django.http import HttpResponse
from django.conf import settings
import json
import hmac
import hashlib
import requests
from base64 import urlsafe_b64decode, urlsafe_b64encode

def fbapi_auth(code):
	params = {'client_id': app.config['FB_APP_ID'],
		'redirect_uri': get_home(),
		'client_secret': app.config['FB_APP_SECRET'],
		'code': code}
		
	result = fbapi_get_string(path=u"/oauth/access_token?", params=params, encode_func=simple_dict_serialisation)
	pairs = result.split("&", 1)
	result_dict = {}
	for pair in pairs:
		(key, value) = pair.split("=")
		result_dict[key] = value
	return (result_dict["access_token"], result_dict["expires"])
	
def get_token(signed_request):
	sig, payload = signed_request.split('.', 2)
	data = json.loads(urlsafe_b64decode(str(payload) + "="*(4 - len(payload) % 4)))
	if not data['algorithm'].upper() == 'HMAC-SHA256':
		raise ValueError('unknown algorithm {0}'.format(data['algorithm']))
	h = hmac.new(settings.FBAPI_APP_SECRET, digestmod=hashlib.sha256)
	h.update(payload)
	expected_sig = urlsafe_b64encode(h.digest()).replace('=', '')
	if sig != expected_sig:
		raise ValueError('bad signature')
	if data.has_key('oauth_token'):
		return data.get('oauth_token')
		
def oauth_redirect():
	return HttpResponse("<script>var oauth_url = 'https://www.facebook.com/dialog/oauth/?client_id={0}&redirect_uri=' + encodeURIComponent('https://apps.facebook.com/{1}/') + '&scope={2}';window.top.location = oauth_url;</script>".format(settings.FBAPI_APP_ID, settings.FBAPI_APP_NAMESPACE, ','.join(settings.FBAPI_SCOPE)))
	
def fb_call(call, args=None):
	url = "https://graph.facebook.com/{0}".format(call)
	r = requests.get(url, params=args)
	return json.loads(r.content)