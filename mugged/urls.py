from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^mugged/$', 'muggedapp.views.index', name='index'),
	url(r'^mugged/mugshot/(?P<id>\d+)', 'muggedapp.views.mugshot', name='mugshot'),
	url(r'^mugged/admin', 'muggedapp.views.admin', name='admin'),
    # url(r'^mugged/', include('mugged.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls))
)
