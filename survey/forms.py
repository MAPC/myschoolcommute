from django.forms import (
    ModelForm, HiddenInput, TextInput,
    IntegerField, CharField, ChoiceField,
)
from django import forms
from django.contrib.gis.geos import Point, GEOSGeometry
# lazy translation
from django.utils.translation import ugettext_lazy as _

from survey.models import (
    Survey, SurveySet, Child, School,
    CHILD_MODES, CHILD_GRADES, CHILD_DROPOFF
)

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit


class SurveyForm(ModelForm):
    """
    Parent Survey Form for collecting basic household information.
    """
    street = ChoiceField(
        label=_('Name of your street'),
        required=False
    )
    cross_st = ChoiceField(
        label=_('Name of nearest cross-street'),
        required=False
    )
    nr_vehicles = ChoiceField(
        label=_('How many vehicles do you have in your household?'),
        choices=[(i, str(i)) for i in range(10)],
        required=False
    )
    nr_licenses = ChoiceField(
        label=_('How many people in your household have a driver\'s license?'),
        choices=[(i, str(i)) for i in range(10)],
        required=False
    )

    location = CharField(widget=HiddenInput())

    def __init__(self, *args, **kwargs):
        if 'school' in kwargs:
            school = kwargs.pop('school')
            super(SurveyForm, self).__init__(*args, **kwargs)
            intersections_all = school.get_intersections()

            intersections = intersections_all.distinct('st_name_1').values('st_name_1')
            choices = [(st, st) for st in [i['st_name_1'].title() for i in intersections]]
            self.fields['street'].choices = choices

            intersections = intersections_all.distinct('st_name_2').values('st_name_2')
            choices = [(st, st) for st in [i['st_name_2'].title() for i in intersections]]
            self.fields['cross_st'].choices = choices

        else:
            super(SurveyForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Survey
        exclude = ('school', 'ip', 'created', 'modified', 'distance', 'user', )


    def clean(self):
        cleaned_data = super(SurveyForm, self).clean()
        wkt = cleaned_data.get('location')

        point = GEOSGeometry(wkt)
        if point.x == 0 or point.y == 0:
            raise forms.ValidationError("Your location is required for the survey.")

        #TODO: Check if two streets return location
        return cleaned_data


class ChildForm(ModelForm):
    """
    Sub-form for collecting information for each child in given school.
    """
    grade = ChoiceField(
        label=_('What grade is your child in?'),
        choices=CHILD_GRADES,
        required=True,
        initial='',
    )
    to_school = ChoiceField(
        label=_('How does your child get TO school on most days?'),
        choices=CHILD_MODES,
        required=True,
    )
    dropoff = ChoiceField(
        label=_('Do you usually drop off your child on your way to work or another destination?'),
        choices=CHILD_DROPOFF,
        required=False,
        initial='',
    )
    from_school = ChoiceField(
        label=_('How does your child get home FROM school on most days?'),
        choices=CHILD_MODES,
        required=True,
    )
    pickup = ChoiceField(
        label=_('Do you usually pick up your child on your way from work or another origin?'),
        choices=CHILD_DROPOFF,
        required=False,
        initial='',
    )

    class Meta:
        model = Child

YES_OR_NO = (
    (True, 'Yes'),
    (False, 'No')
)

class SurveySetForm(ModelForm):
    begin = forms.DateField(
        widget=forms.DateInput(format='%m/%d/%Y'), input_formats=('%m/%d/%Y',)
    )
    end = forms.DateField(
        widget=forms.DateInput(format='%m/%d/%Y'), input_formats=('%m/%d/%Y',)
    )

    def __init__(self, *args, **kwargs):
        super(SurveySetForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'
        self.helper.add_input(Submit('submit', 'Save'))
        self.helper.add_input(Submit('submit', 'Generate Report'))

    class Meta:
        model = SurveySet
        fields = ("begin", "end", )


class SchoolForm(ModelForm):
    survey_active = forms.TypedChoiceField(
        choices=YES_OR_NO, widget=forms.RadioSelect
    )
    #survey_incentive = forms.CharField(label="Survey Form Message", required=False)

    def __init__(self, *args, **kwargs):
        super(SchoolForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'
        self.helper.add_input(Submit('submit', 'Save'))

    class Meta:
        model = School
        fields = ("name", "survey_active", )


class ReportForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(format='%m/%d/%Y'), input_formats=('%m/%d/%Y',))
    end_date = forms.DateField(widget=forms.DateInput(format='%m/%d/%Y'), input_formats=('%m/%d/%Y',))

    def __init__(self, *args, **kwargs):
        super(ReportForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'
        self.helper.form_method = 'get'
        self.helper.add_input(Submit('submit', 'Generate Report'))
        #self.helper.add_input(Submit('submit', 'Download Raw Data'))
