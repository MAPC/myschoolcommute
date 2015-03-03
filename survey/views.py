from django.conf import settings
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import simplejson, dateparse
from django.db.models import Count, Q
from django.forms.models import (
    inlineformset_factory, modelformset_factory, BaseModelFormSet
)
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.contrib.auth.decorators import permission_required

from datetime import datetime, timedelta

from survey.models import (
    School, Survey, SurveySet, SurveySet, Child, District, Street
)
from survey.forms import SurveyForm, BatchForm, SurveySetForm, ChildForm

from maps import ForkRunR

import os


def index(request):

    # get all districts with active school surveys
    active_schools = School.objects.filter(
        Q(surveyset__begin__lte=datetime.now()) &
        Q(surveyset__end__gte=datetime.now())
    )
    districts = District.objects.filter(school__in=active_schools).distinct()

    return render_to_response('survey/index.html', locals(), context_instance=RequestContext(request))


def district(request, district_slug):

    district = District.objects.get(slug__iexact=district_slug)

    return render_to_response('survey/district.html', {
        'district': district,
        'MEDIA_URL': settings.MEDIA_URL,
    }, context_instance=RequestContext(request))


@permission_required('survey.change_district')
def district_list(request):
    districts = District.objects.all()
    districts = districts.annotate(school_count=Count('school', distinct=True))
    districts = districts.annotate(survey_count=Count('school__survey', distinct=True))

    return render_to_response('survey/district_list.html', locals(), context_instance=RequestContext(request))


@login_required
def school_edit(request, district_slug, school_slug, **kwargs):

    # check if district exists
    district = get_object_or_404(District.objects, slug__iexact=district_slug)

    # get school in district
    school = get_object_or_404(School.objects, districtid=district, slug__iexact=school_slug)

    # translate to lat/lon
    school.geometry.transform(4326)

    class BaseSurveySetFormSet(BaseModelFormSet):
        def __init__(self, *args, **kwargs):
            super(BaseSurveySetFormSet, self).__init__(*args, **kwargs)
            self.queryset = SurveySet.objects.filter(school=school).order_by('-begin')

    surveysets = SurveySet.objects.filter(school=school)
    SurveySetFormSet = modelformset_factory(
        SurveySet, formset=BaseSurveySetFormSet, form=SurveySetForm,
        can_delete=True, extra=1
    )

    if request.method == 'POST':
        formset = SurveySetFormSet(request.POST)
        if formset.is_valid():
            sets = formset.save(commit=False)
            for surveyset in sets:
                surveyset.school = school
                surveyset.save()

            formset = SurveySetFormSet()
    else:
        #formset = SurveySetFormSet()
        formset = SurveySetFormSet()

    surveys = Survey.objects.filter(school=school)
    count_day = surveys.filter(created__gte=datetime.today() - timedelta(hours=24)).count()
    count_week = surveys.filter(created__gte=datetime.today() - timedelta(days=7)).count()

    return render_to_response('survey/school_edit.html', {
            'school': school,
            'district': district,
            'surveys': surveys,
            'count_day': count_day,
            'count_week': count_week,
            'formset': formset,
            'surveysets': surveysets,
            'now': datetime.now()
        },
        context_instance=RequestContext(request)
    )

@login_required
def school_report(request, school_id, start, end):
    school = School.objects.get(pk=school_id)
    start_d = dateparse.parse_date(start)
    end_d = dateparse.parse_date(end)

    report_path = "reports/%s/%s_%s_report.pdf" % (
        school.slug, start, end
    )
    full_path = settings.MEDIA_ROOT + '/' + report_path
    full_url = settings.MEDIA_URL + '/' + report_path

    path = ForkRunR(
        school.pk,
        start_d,
        end_d
    )
    dir_name = os.path.dirname(full_path)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    os.rename(path, full_path)

    send_mail(
        "Your report for school %s, date range %s - %s" % (
            school, start, end
        ),
        "You may download it at http://%s/%s" % (
            request.META['HTTP_HOST'], full_url
        ),
        settings.SERVER_EMAIL,
        [request.user.email]
    )

    return HttpResponseRedirect(full_url)


def get_schools(request, districtid):
    """
    Returns all schools for given district as JSON
    """

    # check if district exists
    district = get_object_or_404(District.objects, districtid=districtid)

    schools = School.objects.filter(districtid=district).filter(
        Q(surveyset__begin__lte=datetime.now()) &
        Q(surveyset__end__gte=datetime.now())
    )

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

    street_list = []

    for street in streets:
        street_list.append(street.name)

    return HttpResponse(simplejson.dumps(street_list), mimetype='application/json')


def school_streets(request, school_id, query=None):
    """
    Returns initial list of unique streets within 5000 meters of school
    """

    school = School.objects.get(pk=school_id)
    intersections = school.get_intersections()

    streets = intersections.values('st_name_1').distinct()

    if query is not None and query.strip() != '':
        streets = streets.filter(st_name_1__icontains=query)

    data = [row['st_name_1'].title() for row in list(streets)]

    return HttpResponse(simplejson.dumps(sorted(data)), mimetype='application/json')


def school_crossing(request, school_id, street, query=None):
    """
    Returns list of unique streets within 5000 meters of school crossing
    another street, by name
    """

    school = School.objects.get(pk=school_id)
    intersections = school.get_intersections()

    streets = intersections.filter(st_name_1__iexact=street).values('st_name_2').distinct()

    if query is not None and query.strip() != '':
        streets = streets.filter(st_name_2__icontains=query)

    data = [row['st_name_2'].title() for row in list(streets)]

    return HttpResponse(simplejson.dumps(data), mimetype='application/json')


def intersection(request, school_id, street1, street2=None):
    """
    Returns intersection GeoJSON based on at least one crossing street
    """

    school = School.objects.get(pk=school_id)
    intersections = school.get_intersections()

    intersections = intersections.filter(st_name_1__iexact=street1)

    if street2 is not None and street2.strip() != "":
        intersections = intersections.filter(st_name_2__iexact=street2)

    features = []
    for f in list(intersections.distinct()):
        f.geometry.transform(4326)
        features.append(""" {
            "type": "Feature",
            "geometry": %s,
            "properties": {"id": %d, "street1": "%s", "street2": "%s"}
        }""" % (f.geometry.geojson, f.pk, f.st_name_1.title(), f.st_name_2.title()))

    json_text = """{
    "type": "FeatureCollection",
    "features": [%s]
    }""" % ((",\n").join(features))
    return HttpResponse(json_text)


def form(request, district_slug, school_slug, **kwargs):

    # check if district exists
    district = get_object_or_404(District.objects, slug__iexact=district_slug)

    # get school in district
    school = get_object_or_404(School.objects, districtid=district, slug__iexact=school_slug)

    # translate to lat/lon
    school.geometry.transform(4326)

    SurveyFormset = inlineformset_factory(Survey, Child, form=ChildForm, extra=1, can_delete=False)

    formerror = False

    if request.method == 'POST':
        surveyform = SurveyForm(request.POST, school=school)

        if surveyform.is_valid():
            survey = surveyform.save(commit=False)
            survey.school = school
            survey.update_distance()
            survey.created = datetime.now()
            survey.ip = request.META['REMOTE_ADDR']

            surveyformset = SurveyFormset(request.POST, instance=survey)
            if surveyformset.is_valid():
                survey.save()
                surveyformset.save()

                return render_to_response(
                    'survey/thanks.html',
                    context_instance=RequestContext(request)
                )
            else:
                surveyformset = SurveyFormset(request.POST, instance=Survey())
                formerror = True
        else:
            surveyformset = SurveyFormset(request.POST, instance=Survey())
            formerror = True
    else:
        survey = Survey()
        surveyform = SurveyForm(instance=survey)
        surveyformset = SurveyFormset(instance=survey)

    return render_to_response('survey/form.html', {
            'formerror': formerror,
            'school': school,
            'surveyform': surveyform,
            'surveyformset': surveyformset,
        },
        context_instance=RequestContext(request)
    )

@login_required
def batch_form(request, district_slug, school_slug, **kwargs):

    # check if district exists
    district = get_object_or_404(District.objects, slug__iexact=district_slug)

    # get school in district
    school = get_object_or_404(School.objects, districtid=district, slug__iexact=school_slug)

    # translate to lat/lon
    school.geometry.transform(4326)

    SurveyFormset = inlineformset_factory(Survey, Child, form=ChildForm, extra=1, can_delete=False)

    formerror = False

    message = "New survey"
    if request.method == 'POST':
        surveyform = BatchForm(request.POST, school=school)

        if surveyform.is_valid():
            survey = surveyform.save(commit=False)
            # Ugly Fix: created should save to model, but does not!
            created = surveyform.cleaned_data['created']
            survey.created = created
            survey.user = request.user
            survey.school = school
            survey.update_distance()

            if survey.location is None or survey.location.x == 0:
                survey.update_location()

            survey.ip = request.META['REMOTE_ADDR']

            surveyformset = SurveyFormset(request.POST, instance=survey)
            if surveyformset.is_valid():
                survey.save()
                surveyformset.save()

                #Done. Make new form.
                message = "Survey submitted. New Entry."
                #Save created to reduce repeating
                survey = Survey(created=created)
                surveyform = BatchForm(instance=survey, initial={
                    'created': created
                })
                surveyformset = SurveyFormset(instance=survey)
            else:
                surveyformset = SurveyFormset(
                    request.POST, instance=Survey(created=created)
                )
                formerror = True
        else:
            surveyformset = SurveyFormset(request.POST, instance=Survey())
            formerror = True
    else:
        survey = Survey()
        surveyform = BatchForm(instance=survey)
        surveyformset = SurveyFormset(instance=survey)

    return render_to_response('survey/batch.html', {
            'message': message,
            'formerror': formerror,
            'school': school,
            'surveyform': surveyform,
            'surveyformset': surveyformset,
        },
        context_instance=RequestContext(request)
    )

def testr(request):
    import rpy2.robjects as r
    out = r.r("print('TEST')")
    #out = 'TEST'
    return HttpResponse(out)
