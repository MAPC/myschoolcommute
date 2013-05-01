from django.forms import ModelForm, HiddenInput, TextInput, IntegerField, CharField, ChoiceField

# lazy translation
from django.utils.translation import ugettext_lazy as _

from survey.models import Survey, Child, CHILD_MODES, CHILD_GRADES, CHILD_DROPOFF


class SurveyForm(ModelForm):
    """
    Parent Survey Form for collecting basic household information.
    """
    street = CharField(label=_('Name of your street'),
                    widget = TextInput(attrs={'size': '30'}),
                    required=False,)
    cross_st = CharField(label=_('Name of nearest cross-street'),
                    widget = TextInput(attrs={'size': '30'}),
                    required=False,)
    nr_vehicles = IntegerField(label=_('How many vehicles do you have in your household?'), 
                    widget = TextInput(attrs={'size': '2'}),
                    required=False,)
    nr_licenses = IntegerField(label=_('How many people in your household have a driver\'s license?'),
                    widget = TextInput(attrs={'size': '2'}),
                    required=False,)

    class Meta:
        model = Survey
        exclude = ('school', 'ip', 'created', 'modified', 'distance')
        
        widgets = {
            'location': HiddenInput(),         
        }

class ChildForm(ModelForm):
    """
    Sub-form for collecting information for each child in given school.
    """
    grade = ChoiceField(label=_('What grade is your child in? (<span class="required_field">required</span>)'),
                      choices=CHILD_GRADES,
                      required=True,
                      initial='',)
    to_school = ChoiceField(label=_('How does your child get TO school on most days? (<span class="required_field">required</span>)'),
                      choices=CHILD_MODES,
                      required=True,)
    dropoff = ChoiceField(label=_('Do you usually drop off your child on your way to work or another destination?'),
                      choices=CHILD_DROPOFF,
                      required=False,
                      initial='',)
    from_school = ChoiceField(label=_('How does your child get home FROM school on most days? (<span class="required_field">required</span>)'),
                      choices=CHILD_MODES,
                      required=True,)
    pickup = ChoiceField(label=_('Do you usually pick up your child on your way from work or another origin?'),
                      choices=CHILD_DROPOFF,
                      required=False,
                      initial='',)
    
    class Meta:
        model = Child