from django.conf import settings
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.forms.models import inlineformset_factory
from survey.models import School, Letter, Survey, SurveyForm, Child

from django.template import RequestContext

def index(request, school_slug):
    
    school = School.objects.get(slug__iexact=school_slug)
    letter = Letter.objects.get(pk=1) # only one letter
       
    survey = Survey()   
       
    SurveyFormSet = inlineformset_factory(Survey, Child,  extra=1)
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=survey)
        formset = SurveyFormSet(request.POST, instance=survey)
        # if formset.is_valid():
        #    formset.save()
            # Do something.
    else:
        form = SurveyForm(instance=survey)
        formset = SurveyFormSet(instance=survey)

    return render_to_response('survey/index.html', {
        'school' : school, 
        'letter' : letter,
        'form' : form,
        'formset' : formset,
        },
        context_instance=RequestContext(request)
    )