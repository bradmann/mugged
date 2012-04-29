from django.http import HttpResponse
from django.conf import settings
import json
import hmac
import hashlib
import requests
from base64 import urlsafe_b64decode, urlsafe_b64encode

class FBApi:
	def __init__(self, request):
		if not request.session.has_key('access_token'):	
			request.session['access_token'] = self.get_token(request.POST.get('signed_request'))
		self.access_token = request.session['access_token']
	
	@staticmethod
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
		
	def oauth_redirect(self):
		return HttpResponse("<script>var oauth_url = 'https://www.facebook.com/dialog/oauth/?client_id={0}&redirect_uri=' + encodeURIComponent('https://apps.facebook.com/{1}/') + '&scope={2}';window.top.location = oauth_url;</script>".format(settings.FBAPI_APP_ID, settings.FBAPI_APP_NAMESPACE, ','.join(settings.FBAPI_SCOPE)))
	
	def fb_call(self, call, args=None):
		if self.access_token:
			if args:
				args['access_token'] = self.access_token
			else:
				args = {'access_token': self.access_token}
		url = "https://graph.facebook.com/{0}".format(call)
		r = requests.get(url, params=args)
		return json.loads(r.content)
	
	