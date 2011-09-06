from django.conf import settings
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import simplejson

from django.forms.models import inlineformset_factory

from survey.models import School, Survey, SurveyForm, Child, ChildForm, District, Street

def index(request):
    
    # get all districts with active school surveys
    districts = District.objects.filter(school__survey_active=True).distinct()
    
    return render_to_response('survey/index.html', locals(), context_instance=RequestContext(request))
    
def district(request, district_slug):
    
    district = District.objects.get(slug__iexact=district_slug)
    
    return render_to_response('survey/district.html', {
            'district': district,
            'MEDIA_URL': settings.MEDIA_URL,
            },
            context_instance=RequestContext(request))

def get_schools(request, districtid):
    """
    Returns all schools for given district as JSON
    """
    
    # check if district exists
    district = get_object_or_404(District.objects, districtid=districtid)
    
    schools = School.objects.filter(districtid=district)
    
    response = {}
    
    for school in schools:
        response[school.id] = dict(name=school.name, url=school.get_absolute_url())

    return HttpResponse(simplejson.dumps(response), mimetype='application/json')   
    
    
def get_streets(request, districtid):
    """
    Returns all streets for given district
    """
    
    # check if district exists
    district = get_object_or_404(District.objects, districtid=districtid)
    
    streets = Street.objects.filter(districtid=districtid)
    
    street_list =[]
    
    for street in streets:
        street_list.append(street.name)
    
    return HttpResponse(simplejson.dumps(street_list), mimetype='application/json')


def form(request, district_slug, school_slug, **kwargs):
    
    # check if district exists
    district = get_object_or_404(District.objects, slug__iexact=district_slug)
    
    # get school in district
    school = get_object_or_404(School.objects, districtid=district, slug__iexact=school_slug)
    
    # translate to lat/lon
    school.geometry.transform(4326)
       
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
                },
                context_instance=RequestContext(request)
            )
            
        else:
            return render_to_response('survey/form.html', {
                'formerror': True,
                'school' : school, 
                'surveyform' : surveyform,
                'surveyformset' : surveyformset,
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
            },
            context_instance=RequestContext(request)
        )