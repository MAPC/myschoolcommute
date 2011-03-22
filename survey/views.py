from django.conf import settings
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.forms import ModelForm
from survey.models import School, Letter

from django.template import RequestContext

def index(request, school_slug):
    
    school = School.objects.get(slug__iexact=school_slug)
    letter = Letter.objects.get(pk=1) # only one letter
    
    return render_to_response('survey/index.html', 
                              {'school' : school, 
                               'letter' : letter}, 
                              context_instance=RequestContext(request))