import json
import requests
	
def fb_call(call, args=None):
	url = "https://graph.facebook.com/{0}".format(call)
	r = requests.get(url, params=args)
	return json.loads(r.content)
	
def get_friends(request):
	access_token = request.session['access_token']
	friends = fb_call('me/friends', args={'access_token': access_token})
	friendarr = friends['data']
	while friends.has_key('paging') and friends['paging'].has_key('next'):
		next_url = friends['paging']['next']
		r = requests.get(next_url, params={'access_token': access_token})
		friends = json.loads(r.content)
		friendarr.extend(friends['data'])
	return friendarr
	
def get_user(request, id):
	access_token = request.session['access_token']
	return fb_call(str(id), args={'access_token': access_token})