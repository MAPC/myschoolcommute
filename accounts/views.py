from django.template import RequestContext, loader
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.contrib.auth import authenticate, login, logout
from django.forms.models import model_to_dict
from models import Profile
from forms import LoginForm, RegistrationForm, ProfileForm, UserForm
from django.utils.html import escape
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.forms import ValidationError
from django.core.mail import send_mail, mail_managers, mail_admins
from django.conf import settings

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Layout, Fieldset, ButtonHolder, Submit


def index(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect('/accounts/profile/')
    else:
        return HttpResponseRedirect('/accounts/login/')


def register(request):
    if request.method == 'POST':
        user_form = RegistrationForm(request.POST)
        profile_form = ProfileForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            new_user = user_form.save()
            p = Profile.objects.get(user=new_user)
            profile_form = ProfileForm(request.POST, instance=p)
            profile_form.save()

            users_page = 'http://' + request.META['HTTP_HOST'] + reverse('user_list')
            approve_page = 'http://' + request.META['HTTP_HOST'] + reverse('user_edit', args=[new_user.username])
            message = "New user registration!\n\n%s\n%s, %s\nActivate user: %s\nView all users: %s" % (
                new_user.username, new_user.first_name, new_user.last_name, approve_page, users_page,
            )

            try:
                g = Group.objects.get(name="MassRIDES Staff")
                emails = [u.email for u in g.user_set.all()]
                send_mail(
                    'myschoolcommute.com new user '+new_user.username,
                    message,
                    settings.SERVER_EMAIL,
                    emails
                )
            except:
                #Problem finding group or emailing
                mail_admins('myschoolcommute.com new user '+new_user.username, message)

            return HttpResponseRedirect("/accounts/register/success/")
    else:
        profile_form = ProfileForm()
        user_form = RegistrationForm()

    profile_form.helper.add_input(Submit('submit', 'Create the account'))
    return render_to_response("accounts/register.html", {
        'user_form' : user_form, 'profile_form': profile_form
    }, context_instance=RequestContext(request))


def register_success(request):
    return render_to_response("accounts/register_success.html",
        context_instance=RequestContext(request)
    )


def profile_authed(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('user_detail', args=[request.user.username]))
    else:
        return HttpResponseRedirect('/accounts/login/')


def profile(request, username):
    if request.user.is_authenticated():
        u = User.objects.get(username=username)
        p = u.get_profile()

        user_form = UserForm(instance=u)
        user_form.merge_from_initial()

        return render_to_response('accounts/profile.html',
        {
            'username': u.username,
            'user_f': user_form,
            'profile': p
        }, context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect('/')


@login_required
def profile_edit(request, username=None):
    if username is None:
        p = request.user.get_profile()
        user = request.user
    else:
        user = User.objects.get(username=username)
        p = user.get_profile()

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        profile_form = ProfileForm(request.POST, instance=p, editor=request.user)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            p = profile_form.save()

            if 'is_active' in request.POST and request.user.has_perm('auth.change_user'):
                user.is_active = True
                user.save()
                send_mail(
                    "Your myschoolcommute.com account has been approved",
                    "You may login at http://%s/%s" % (request.META['HTTP_HOST'], reverse('login'),),
                    settings.SERVER_EMAIL,
                    [user.email]
                )

            return HttpResponseRedirect(reverse('user_detail', args=[user.username]))
    else:
        user_form = UserForm(instance=user)
        profile_form = ProfileForm(instance=p, editor=request.user)

    profile_form.helper.add_input(Submit('submit', 'Save account'))

    return render_to_response("accounts/edit.html", {
        'user_form' : user_form, 'profile_form': profile_form, 'user': user
    }, context_instance=RequestContext(request) )

