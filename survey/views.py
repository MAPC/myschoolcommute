from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.forms import ModelForm
from survey.models import School

from django.template import RequestContext

def school(request, school_slug):
    
    school = School.objects.get(slug__iexact=school_slug)
    
    return HttpResponse("Schoolname: %s location: %s" % (school.name, school.location))