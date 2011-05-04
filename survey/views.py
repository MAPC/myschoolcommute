from django.conf import settings
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.forms.models import inlineformset_factory
from survey.models import School, Survey, SurveyForm, Child, ChildForm, District

from django.template import RequestContext

def index(request):
    
    # get all districts with active school surveys
    districts = District.objects.filter(school__survey_active=True).distinct()
    
    return render_to_response('survey/index.html', {
            'districts': districts,
            'MEDIA_URL': settings.MEDIA_URL,
            },
            context_instance=RequestContext(request)
        )
    
def district(request, district_slug):
    
    district = District.objects.get(slug__iexact=district_slug)
    
    return render_to_response('survey/district.html', {
            'district': district,
            'MEDIA_URL': settings.MEDIA_URL,
            },
            context_instance=RequestContext(request))

def form(request, school_slug, **kwargs):
    
    school = School.objects.get(slug__iexact=school_slug)
       
    survey = Survey()   
       
    SurveyFormset = inlineformset_factory(Survey, Child, form=ChildForm, extra=1, can_delete=False)
    
    if request.method == 'POST':
        surveyform = SurveyForm(request.POST, instance=survey)
        surveyformset = SurveyFormset(request.POST, instance=survey)
        survey.school = school
        survey.ip = request.META['REMOTE_ADDR']
        
        
        if surveyformset.is_valid() and surveyform.is_valid():
            surveyform.save()
            surveyformset.save()
            
            return render_to_response('survey/thanks.html', {
                'MEDIA_URL': settings.MEDIA_URL,
                },
                context_instance=RequestContext(request)
            )
            
        else:
            return render_to_response('survey/form.html', {
                'formerror': True,
                'school' : school, 
                'surveyform' : surveyform,
                'surveyformset' : surveyformset,
                'MEDIA_URL': settings.MEDIA_URL,
                },
                context_instance=RequestContext(request)
            )
    else:
        surveyform = SurveyForm(instance=survey)
        surveyformset = SurveyFormset(instance=survey)

        return render_to_response('survey/form.html', {
            'school' : school, 
            'surveyform' : surveyform,
            'surveyformset' : surveyformset,
            'MEDIA_URL': settings.MEDIA_URL,
            },
            context_instance=RequestContext(request)
        )