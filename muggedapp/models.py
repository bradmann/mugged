from django.db import models
from djangotoolbox.fields import ListField, EmbeddedModelField, DictField

from django_mongodb_engine.storage import GridFSStorage
import datetime
gridfs_storage = GridFSStorage()

class FacebookUser(models.Model):
	fbid = models.CharField(max_length=255, db_index=True)
	mugshots = ListField(EmbeddedModelField('Mugshot'))
	
	def __unicode__(self):
		return self.fbid

class AdminDocument(models.Model):
	name = models.CharField(max_length=255)
	document = DictField()

class MugshotSearch(models.Model):
	fname = models.CharField(max_length=255, db_index=True)
	mname = models.CharField(max_length=255, blank=True, null=True, db_index=True)
	lname = models.CharField(max_length=255, db_index=True)
	birthdate = models.DateField(blank=True, null=True, db_index=True)
	gender = models.CharField(max_length=1, blank=True, null=True, db_index=True)
	last_searched = models.DateTimeField(default=datetime.datetime(1970,1,1), db_index=True)
	results = ListField(EmbeddedModelField('MugshotSearchResult'))
	
	class Meta:
		unique_together = ('fname', 'lname', 'birthdate', 'gender')
		
	def search_requests(self):
		requests = [{'fname': self.fname, 'lname': self.lname}]
		if self.mname: requests.append({'fname': self.fname, 'lname': self.mname.strip('-')})
		if '-' in self.lname:
			requests.append({'fname': self.fname, 'lname': self.lname.split('-')[0]})
			requests.append({'fname': self.fname, 'lname': self.lname.split('-')[1]})
		if ' ' in self.lname:
			requests.append({'fname': self.fname, 'lname': self.lname.split(' ')[0]})
			requests.append({'fname': self.fname, 'lname': self.lname.split(' ')[1]})
		for req in requests:
			req['fpartial'] = True
			req['startdate'] = self.last_searched.strftime('%m/%d/%Y')
			if self.gender: req['sex'] = self.gender
			if self.birthdate:
				age = int((datetime.date.today() - self.birthdate).days / 365.25)
				req['minage'] = age
				req['maxage'] = age
		return requests
		
class MugshotSearchResult(models.Model):
	thumbpath = models.URLField(max_length=1023)
	arrestpath = models.URLField(max_length=1023)
	matches_user = models.CharField(max_length=255, blank=True, null=True)
	not_matched = ListField(models.CharField(max_length=255))

class Mugshot(models.Model):
	name = models.CharField(max_length=768)
	arrest_date = models.DateTimeField(blank=True, null=True)
	charges = models.TextField(blank=True, null=True)
	description = models.CharField(max_length=2047, blank=True, null=True)
	mugshot_image = models.FileField(storage=gridfs_storage, upload_to='/')
	race = models.CharField(max_length=255, blank=True, null=True)
	
	def __unicode__(self):
		return self.name