from django.db import models

class FacebookUser(models.Model):
	fbid = models.CharField(primary_key=True, max_length=255)
	
	def __unicode__(self):
		return self.fbid	

class MugshotSearch(models.Model):
	fbuser = models.ForeignKey('FacebookUser')
	fname = models.CharField(max_length=255)
	lname = models.CharField(max_length=255)
	birthdate = models.CharField(max_length=20)
	gender = models.CharField(max_length=1)
	last_searched = models.DateTimeField()
	
	class Meta:
		unique_together = ('fname', 'lname', 'birthdate', 'gender')
		
class MugshotSearchResult(models.Model):
	search = models.ForeignKey('MugshotSearch')
	thumbpath = models.URLField(max_length=1023)
	arrestpath = models.URLField(max_length=1023)
	
class Arrest(models.Model):
	fbuser = models.ForeignKey(FacebookUser)
	name = models.CharField(max_length=255)
	arrest_date = models.DateTimeField()
	charges = models.TextField()
	location = models.CharField(max_length=1023)
	mugshot = models.ImageField(upload_to='mugshots')
	
	def __unicode__(self):
		return self.name