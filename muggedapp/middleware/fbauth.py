from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from base64 import urlsafe_b64decode, urlsafe_b64encode
import hmac
import hashlib
import json
import urllib
import urlparse
import requests
import datetime

oauth_uri = 'https://www.facebook.com/dialog/oauth?client_id=' + settings.FBAPI_APP_ID + '&scope=' + ','.join(settings.FBAPI_SCOPE)
at_uri = 'https://graph.facebook.com/oauth/access_token?client_id=' + settings.FBAPI_APP_ID + '&client_secret=' + settings.FBAPI_APP_SECRET

class FBAuthMiddleware:
	def get_token(self, signed_request):
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

	def process_request(self, request):
		if request.method == 'POST':
			signed_request = request.POST.get('signed_request', None)
			if not signed_request:
				return None
			access_token = self.get_token(signed_request)
			if not access_token:
				return self.oauth_redirect()
			else:
				request.session['access_token'] = access_token
				return None
		elif request.method == 'GET':
			code = request.GET.get('code')
			access_token = request.session.get('access_token')
			expires = request.session.get('expires')
			if (expires and datetime.datetime.now() > expires) or (not access_token and not code):
				return HttpResponseRedirect(oauth_uri + '&redirect_uri=' + request.build_absolute_uri() + '&state=login')
			elif code:
				req = requests.get(at_uri + '&redirect_uri=' + request.build_absolute_uri() + '&code=' + code)
				logger.error(req.text)
				if req.status_code == 200:
					d = urlparse.parse_qs(req.text)
					request.session['access_token'] = d['access_token'][0]
					request.session['expires'] = datetime.datetime.now() + datetime.timedelta(seconds=int(d['expires'][0]) - 20)
					return None
				else:
					return HttpResponse('Error retreiving Facebook access_token.')
			else:
				return None