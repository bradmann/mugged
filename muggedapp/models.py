from django.db import models
import datetime

class FacebookUser(models.Model):
	fbid = models.CharField(primary_key=True, max_length=255)
	
	def __unicode__(self):
		return self.fbid	

class MugshotSearch(models.Model):
	fbuser = models.ForeignKey(FacebookUser)
	fname = models.CharField(max_length=255)
	mname = models.CharField(max_length=255, blank=True, null=True)
	lname = models.CharField(max_length=255)
	birthdate = models.DateField(blank=True, null=True)
	gender = models.CharField(max_length=1, blank=True, null=True)
	last_searched = models.DateTimeField(default=datetime.datetime(1970,1,1))
	
	class Meta:
		unique_together = ('fbuser', 'fname', 'lname', 'birthdate', 'gender')
		
	def search_requests(self):
		requests = [{'fname': self.fname, 'lname': self.lname}]
		if self.mname: requests.append({'fname': self.fname, 'lname': self.mname.strip('-')})
		if '-' in self.lname:
			requests.append({'fname': self.fname, 'lname': self.lname.split('-')[0]})
			requests.append({'fname': self.fname, 'lname': self.lname.split('-')[1]})
		for req in requests:
			req['fpartial'] = True
			req['startdate'] = self.last_searched.strftime('%m%%2F%d%%2F%Y')
			if self.gender: req['sex'] = self.gender
			if self.birthdate:
				age = int((datetime.date.today() - self.birthdate).days / 365.25)
				req['minage'] = age
				req['maxage'] = age
		return requests
		
class MugshotSearchResult(models.Model):
	search = models.ForeignKey(MugshotSearch)
	thumbpath = models.URLField(max_length=1023)
	arrestpath = models.URLField(max_length=1023)
	matches_user = models.NullBooleanField()

class Arrest(models.Model):
	fbuser = models.ForeignKey(FacebookUser)
	name = models.CharField(max_length=255)
	arrest_date = models.DateTimeField()
	charges = models.TextField()
	location = models.CharField(max_length=1023)
	mugshot = models.ImageField(upload_to='mugshots')
	
	def __unicode__(self):
		return self.name