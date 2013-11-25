from django.conf.urls import url, include, patterns
from django.contrib.auth.models import User
from django.views.generic import ListView
from forms import LoginForm

from views import *

urlpatterns = patterns('',
    url(r'^$', index, name='accounts'),

    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'accounts/login.html', 'authentication_form': LoginForm}, name='login'),
    (r'^logout/$', 'django.contrib.auth.views.logout', {'template_name': 'accounts/logout.html'}),

    url(r'^register/$', register, name='register'),
    url(r'^register/success/$', register_success, name='register_success'),

    (r'^password/change/$', 'django.contrib.auth.views.password_change', {'template_name': 'accounts/password_change_form.html'}),
    (r'^password/done/$', 'django.contrib.auth.views.password_change_done', {'template_name': 'accounts/password_change_done.html'}),

    (r'^reset/$', 'django.contrib.auth.views.password_reset', {'template_name': 'accounts/password_reset_form.html'}),
    (r'^reset/done/$', 'django.contrib.auth.views.password_reset_done', {'template_name': 'accounts/password_reset_done.html'}),
    (r'^reset/token/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'django.contrib.auth.views.password_reset_confirm', {'template_name': 'accounts/password_reset_confirm.html'}),
    (r'^reset/complete/$', 'django.contrib.auth.views.password_reset_complete', {'template_name': 'accounts/password_reset_complete.html'}),

    (r'^profile/$', profile_authed),
    url(r'^edit/$', profile_edit),
    url(r'^edit/(?P<username>\w+)/$', profile_edit, name='user_edit'),
    url(r'^profile/(?P<username>\w+)/$', profile, name='user_detail'),

    url(r'^users/$',
        ListView.as_view(
            queryset=User.objects.all(),
            context_object_name='object_list',
            template_name='accounts/user_list.html'
        ), name='user_list'
    ),
)
