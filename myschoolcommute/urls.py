from django.conf.urls import patterns, url, include
from django.conf import settings
from django.views.generic import TemplateView

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^walkboston/', include('walkboston.foo.urls')),

    (r'^admin/', include(admin.site.urls)),
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Translation app
    (r'^rosetta/', include('rosetta.urls')),

    #Accounts
    (r'^accounts/', include('accounts.urls')),

    # district/school list on front-page
    (r'^$', 'survey.views.index'),

    # static pages
    (r'^about/$', TemplateView.as_view(template_name='survey/about.html')),

    # custom admin pages
    url(r'^districts/$', 'survey.views.district_list', name='district_list'),
    url(r'^(?P<district_slug>[-\w]+)/(?P<school_slug>[-\w]+)/edit/$', 'survey.views.school_edit', name='school_edit'),
    url(r'^(?P<school_id>\d+)/walkshed.png$', 'survey.maps.school_sheds', name='school_sheds'),
    url(r'^(?P<school_id>\d+)/walkshed.geojson$', 'survey.maps.school_sheds_json', name='sheds_json'),
    url(r'^(?P<school_id>\d+)/(?P<zoom>\d+)/(?P<column>\d+)/(?P<row>\d+)/walkshed.png$', 'survey.maps.school_tms', name='school_tms'),
    url(r'^walk/(?P<zoom>\d+)/(?P<column>\d+)/(?P<row>\d+)/walk.png$', 'survey.maps.walks', name='walk_tms'),

    # district
    (r'^(?P<district_slug>[-\w]+)/$', 'survey.views.district'),
    url(r'^(?P<districtid>[-\w]+)/schools/$', 'survey.views.get_schools', name='disctrict_get_schools'),
    url(r'^(?P<districtid>[-\w]+)/streets/$', 'survey.views.get_streets', name='disctrict_get_streets'),

    # school
    url(r'^(?P<district_slug>[-\w]+)/(?P<school_slug>[-\w]+)/$', 'survey.views.form', name='survey_school_form'),

    #Typeahead
    url(r'^(?P<school_id>\d+)/streets/(?P<query>[\s\w]+)/$', 'survey.views.school_streets'),
    url(r'^(?P<school_id>\d+)/crossing/(?P<street>[\s\w]+)/$', 'survey.views.school_crossing' ),
    url(r'^(?P<school_id>\d+)/crossing/(?P<street>[\s\w]+)/(?P<query>[\s\w]+)/$', 'survey.views.school_crossing' ),
    url(r'^(?P<school_id>\d+)/intersection/(?P<street1>[\s\w]+)/$', 'survey.views.intersection' ),
    url(r'^(?P<school_id>\d+)/intersection/(?P<street1>[\s\w]+)/(?P<street2>[\s\w]+)/$', 'survey.views.intersection' ),
)
