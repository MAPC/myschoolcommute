from django.conf.urls.defaults import *
from django.conf import settings
from django.views.generic.simple import direct_to_template

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^walkboston/', include('walkboston.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    
    # Translation app
    (r'^rosetta/', include('rosetta.urls')),
    
    # district/school list on front-page
    (r'^$', 'survey.views.index'),
    
    # static pages
    (r'^about/$', direct_to_template, {'template': 'survey/about.html'}),
    
    # district
    (r'^(?P<district_slug>[-\w]+)/$', 'survey.views.district'),
    url(r'^(?P<districtid>[-\w]+)/schools/$', 'survey.views.get_schools', name='disctrict_get_schools'),
    url(r'^(?P<districtid>[-\w]+)/streets/$', 'survey.views.get_streets', name='disctrict_get_streets'),
    # school
    url(r'^(?P<district_slug>[-\w]+)/(?P<school_slug>[-\w]+)/$', 'survey.views.form', name='survey_school_form'),    
)


