from django.conf.urls.defaults import *
from django.conf import settings
from django.views.generic import TemplateView

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^walkboston/', include('walkboston.foo.urls')),

    (r'^admin/', include(admin.site.urls)),
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    
    # Translation app
    (r'^rosetta/', include('rosetta.urls')),
    
    # district/school list on front-page
    (r'^$', 'survey.views.index'),
    
    # static pages
    (r'^about/$', TemplateView.as_view(template_name='survey/about.html')),
    
    # district
    (r'^(?P<district_slug>[-\w]+)/$', 'survey.views.district'),
    url(r'^(?P<districtid>[-\w]+)/schools/$', 'survey.views.get_schools', name='disctrict_get_schools'),
    url(r'^(?P<districtid>[-\w]+)/streets/$', 'survey.views.get_streets', name='disctrict_get_streets'),
    # school
    url(r'^(?P<district_slug>[-\w]+)/(?P<school_slug>[-\w]+)/$', 'survey.views.form', name='survey_school_form'),    
)


