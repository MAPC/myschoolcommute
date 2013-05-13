from django.template import RequestContext, loader
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.contrib.auth import authenticate, login, logout
from django.forms.models import model_to_dict
from models import Profile
from forms import LoginForm, RegistrationForm, ProfileForm, UserForm
from django.utils.html import escape
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.forms import ValidationError

def index(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect('/accounts/profile/')
    else:
        return HttpResponseRedirect('/accounts/login/')

def logout(request):
    logout(request)
    return HttpResponseRedirect('/')

def register(request):
    if request.method == 'POST':
        user_form = RegistrationForm(request.POST)
        profile_form = ProfileForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            new_user = user_form.save()
            p = Profile.objects.get(user=new_user)
            profile_form = ProfileForm(request.POST, instance=p)
            profile_form.save()
            
            user = authenticate(username=request.POST['username'], password=request.POST['password1'])
            if user is not None:
                login(request,user)
                
            return HttpResponseRedirect("/accounts/profile/")
    else:
        profile_form = ProfileForm()
        user_form = RegistrationForm()

    return render_to_response("accounts/register.html", {
        'user_form' : user_form, 'profile_form': profile_form
    }, context_instance=RequestContext(request))


def profile_authed(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('user_detail', args=[request.user.username]))
    else:
        return HttpResponseRedirect('/accounts/login/')

def profile(request, username):
    if request.user.is_authenticated():
        u = User.objects.get(username=username)
        p = Profile.objects.get(user=u)

        user_form = UserForm(instance=u)      
        user_form.merge_from_initial()

        return render_to_response('accounts/profile.html',
        {
            'username': u.username,
            'user_f': user_form, 
            'profile': p,
        }, context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect('/')

@login_required
def profile_edit(request):
    p = request.user.get_profile()

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, instance=p)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            p = profile_form.save()
            return HttpResponseRedirect(reverse('user_detail', args=[request.user.username]))
    else:
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=p)
        
    return render_to_response("accounts/edit.html", {
        'user_form' : user_form, 'profile_form': profile_form
    }, context_instance=RequestContext(request) )

def add_place(request):
    if request.method == "POST":
        form = WorkplaceForm(request.POST)
        if form.is_valid():
            try:
                new = form.save()
            except ValidationError, error:
                new = None
            if new:
                return HttpResponse('<script type="text/javascript">opener.dismissAddAnotherPopup(window, "%s", "%s");</script>' % \
                        (escape(new._get_pk_val()), escape(new)))
    else:
        form = WorkplaceForm()
    
    context = {'form':form, 'field':'place'}
    return render_to_response("add_popup.html", context)
