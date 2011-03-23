from django.conf import settings
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.forms.models import inlineformset_factory
from survey.models import School, Survey, SurveyForm, Child

from django.template import RequestContext

def index(request, school_slug):
    
    school = School.objects.get(slug__iexact=school_slug)
       
    survey = Survey()   
       
    SurveyFormSet = inlineformset_factory(Survey, Child, extra=1, can_delete=False)
    
    if request.method == 'POST':
        surveyform = SurveyForm(request.POST, instance=survey)
        surveyformset = SurveyFormSet(request.POST, instance=survey)
        # if formset.is_valid():
        #    formset.save()
            # Do something.
    else:
        surveyform = SurveyForm(instance=survey)
        surveyformset = SurveyFormSet(instance=survey)

    return render_to_response('survey/index.html', {
        'school' : school, 
        'surveyform' : surveyform,
        'surveyformset' : surveyformset,
        },
        context_instance=RequestContext(request)
    )