from muggedapp.models import FacebookUser, MugshotSearch, MugshotSearchResult, Mugshot
from bs4 import BeautifulSoup

import datetime
import requests
import re

base_uri = 'http://florida.arrests.org'
search_uri = base_uri + '/search.php'
	
def get_birthdate(birthday):
	if not birthday or len(birthday.split('/')) != 3:
		return None
	month, day, year = birthday.split('/')
	return datetime.date(int(year), int(month), int(day))
	
def verify(id, mugshot):
	ms = MugshotSearchResult.objects.filter(search__fbuser__fbid=id).get(arrestpath=mugshot)
	ms.matches_user = True
	ms.save()
	data = scrape_mugshot(base_uri + mugshot)
	Mugshot.objects.create(result=ms, name=data.get('name'), arrest_date=data.get('arrest_date'), charges=data.get('charges'),
		description=data.get('description'), race=data.get('race'), mugshot_image=data.get('mugshot_image'))
	
def reject(id, mugshot):
	mugshot = MugshotSearchResult.objects.filter(search__fbuser__fbid=id).get(arrestpath=mugshot)
	mugshot.matches_user = False
	mugshot.save()

def reject_all(id):
	mugshots = MugshotSearchResult.objects.filter(search__fbuser__fbid=id, matches_user=None)
	mugshots.update(matches_user=False)
	
def verify_all(id):
	mugshots = MugshotSearchResult.objects.filter(search__fbuser__fbid=id, matches_user=None)
	mugshots.update(matches_user=True)

def search_and_update(fbuser):
	id = fbuser['id']
	fname = fbuser.get('first_name')
	mname = fbuser.get('middle_name')
	lname = fbuser.get('last_name')
	birthday = fbuser.get('birthday')
	birthdate = get_birthdate(birthday)
	gender = {'male': 'M', 'female': 'F'}.get(fbuser.get('gender'))
	
	dbUser, created = FacebookUser.objects.get_or_create(fbid=id)

	dbSearch = MugshotSearch.objects.filter(fname=fname, mname=mname, lname=lname, birthdate=birthdate, gender=gender)
	if dbSearch.count() == 0:
		MugshotSearch.objects.create(fname=fname, mname=mname, lname=lname, birthdate=birthdate, gender=gender)
		dbSearch = MugshotSearch.objects.filter(fname=fname, mname=mname, lname=lname, birthdate=birthdate, gender=gender)
	for search in dbSearch:
		if search.last_searched < (datetime.datetime.now() - datetime.timedelta(1)):
			for request_params in search.search_requests():
				results = search_mugshot_web(request_params)
				search_results = []
				for result in results:
					search_results.append(MugshotSearchResult.objects.create(thumbpath=result['thumbpath'], arrestpath=result['arrestpath']))
				search.results.extend(search_results)
			search.last_searched = datetime.datetime.now()
			search.save()
	mugsearches = []
	for mss in MugshotSearch.objects.filter(fname=fname, mname=mname, lname=lname, birthdate=birthdate, gender=gender):
		for s in mss.results:
			if not s.matches_user or s.matches_user == True:
				mugsearches.append(s)
	return mugsearches

def search_mugshot_web(request_params):
	req = requests.get(search_uri, params=request_params)
	page = req.content
	imgpaths = re.findall("<img src='(/thumbs/[^']*)'", page)
	arrestpaths = re.findall("<a href='(/Arrests/[^']*)'", page)
	if len(imgpaths) == 0:
		return []
	paths = [{'thumbpath': imgpaths[i], 'arrestpath': arrestpaths[i], 'matches_user': None} for i in xrange(len(imgpaths))]
	pagenum = 1
	patharr = paths[:]
	while len(paths) == 42:
		request_params['page'] = pagenum
		req = requests.get(search_uri, params=request_params)
		page = req.content
		imgpaths = re.findall("<img src='(/thumbs/[^']*)'", page)
		arrestpaths = re.findall("<a href='(/Arrests/[^']*)'", page)
		paths = [{'thumbpath': imgpaths[i], 'arrestpath': arrestpaths[i], 'matches_user': None} for i in xrange(len(imgpaths))]
		patharr.extend(paths)
		pagenum += 1
	return patharr
	
def scrape_mugshot(uri):
	req = requests.get(uri)
	html = req.content
	soup = BeautifulSoup(html)
	tables = soup.findAll('table', id='info')
	vals = {}
	nameCell = soup.findAll('td', {'colspan': 4})[0].text
	vals['name'] = nameCell
	vals['description'] = soup.find('meta', attrs={'name': 'description'})['content']
	for t in tables:
		rows = t.findAll('tr')
		for row in rows:
			tds = row.findAll('td', {'colspan': None})
			cells = [tds[i] for i in xrange(0, len(tds), 2)]
			for cell in cells:
				if cell.b != None and cell.b.string != '&nbsp;':
					nextCell = cell.findNextSiblings('td')[0]
					vals[cell.b.string.strip().lower().replace(' ', '_')] = nextCell.text.lstrip(':').replace('&nbsp;', ' ').replace('&quot;', '"').strip()
	arrDate = vals['arrest_date'].split('-')
	vals['arrest_date'] = datetime.datetime(int(arrDate[2]), int(arrDate[0]), int(arrDate[1]))
	match = re.search("'(/mugs/[^']*)", html)
	vals['mugshot_image'] = match.group(1)
	vals['charges'] = ''
	headers = soup.findAll('div', id='fadebarsmall')
	for header in headers:
		if header.string == 'Charges':
			for sib in header.next_siblings:
				if not hasattr(sib, 'name'):
					vals['charges'] += sib
				elif sib.name != 'div':
					if sib.string: vals['charges'] += sib.string
				else:
					break
	return vals