from django.db import models

class FacebookUser(models.Model):
	fbid = models.CharField(max_length=255)
	name = models.CharField(max_length=255)
	avatar_url = models.URLField(max_length=1023)
	last_searched = models.DateTimeField()
	
	def __unicode__(self):
		return self.name
	

class Arrest(models.Model):
	fbuser = models.ForeignKey(FacebookUser)
	name = models.CharField(max_length=255)
	arrest_date = models.DateTimeField()
	charges = models.TextField()
	location = models.CharField(max_length=1023)
	mugshot = models.ImageField(upload_to='mugshots')
	
	def __unicode__(self):
		return self.name