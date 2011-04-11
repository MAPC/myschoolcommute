from django.conf import settings
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.forms.models import inlineformset_factory
from survey.models import School, Survey, SurveyForm, Child, ChildForm

from django.template import RequestContext

def index(request):
    
    schools = School.objects.all().order_by('name')
    
    return render_to_response('survey/index.html', {
            'schools' : schools, 
            },
            context_instance=RequestContext(request)
        )

def form(request, school_slug):
    
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
            
            return HttpResponse("success. thank you!")
            
        else:
            pass
    else:
        surveyform = SurveyForm(instance=survey)
        surveyformset = SurveyFormset(instance=survey)

        return render_to_response('survey/form.html', {
            'school' : school, 
            'surveyform' : surveyform,
            'surveyformset' : surveyformset,
            },
            context_instance=RequestContext(request)
        )