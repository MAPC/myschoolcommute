from django.contrib.gis.db import models
from django.forms import ModelForm, HiddenInput, TextInput, IntegerField, CharField, ChoiceField

# workaround for South custom fields issues 
try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ['^django\.contrib\.gis\.db\.models\.fields\.PointField'])
except ImportError:
    pass

class School(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField()
    # GeoDjango
    location = models.PointField(geography=True) # default SRS 4326
    objects = models.GeoManager()
    
    def __unicode__(self):
        return self.name
             
class Survey(models.Model):
    school = models.ForeignKey('School')
    street = models.CharField(max_length=50, blank=True, null=True)
    cross_st = models.CharField('Cross street', max_length=50, blank=True, null=True)
    nr_vehicles = models.IntegerField('Number of Vehicles', blank=True, null=True)
    nr_licenses = models.IntegerField('Number of License', blank=True, null=True)
    ip = models.IPAddressField('IP Address', blank=True, null=True)
    # GeoDjango
    location = models.PointField(geography=True, blank=True, null=True, default='POINT(0 0)') # default SRS 4326
    objects = models.GeoManager()
    
    def __unicode__(self):
        return u'%s' % (self.id)

class SurveyForm(ModelForm):
    street = CharField(label='Your street',
                       required=False,)
    cross_st = CharField(label='Cross-street',
                         required=False,)
    nr_vehicles = IntegerField(label='How many vehicles do you have in your household?', 
                               widget = TextInput(attrs={'size': '2'}),
                               required=False,)
    nr_licenses = IntegerField(label='How many people in your household have a driver\'s license?',
                               widget = TextInput(attrs={'size': '2'}),
                               required=False,)

    class Meta:
        model = Survey
        exclude = ('school', 'ip')
        
        widgets = {
            'location': HiddenInput(),         
        }

CHILD_GRADES = (
            ('', '--'),
            ('p', 'Pre-K'),
            ('k', 'K'),
            ('1', '1st'),
            ('2', '2nd'),
            ('3', '3rd'),
            ('4', '4th'),
            ('5', '5th'),
            ('6', '6th'),
            ('7', '7th'),
            ('8', '8th'),
            )
CHILD_MODES = (
            ('', '--'),
            ('w', 'Walk'),
            ('b', 'Bike'),
            ('sb', 'School bus'),
            ('fv', 'Family Vehicle (only children in your family)'),
            ('cp', 'Carpool (with children from other families)'),
            ('t', 'Transit (city bus, subway, etc.)'),
            ('o', 'Other (skateboard, scooter, inline skates, etc.)')
            )
CHILD_DROPOFF = (
            ('', '--'),
            ('yes', 'Yes'),
            ('no', 'No'),
            )
    
class Child(models.Model):
    survey = models.ForeignKey('Survey')
    grade = models.CharField(max_length=1, blank=True, null=True, choices=CHILD_GRADES)
    to_school = models.CharField(max_length=2, blank=True, null=True, choices=CHILD_MODES)
    from_school = models.CharField(max_length=2, blank=True, null=True, choices=CHILD_MODES)
    dropoff = models.CharField(max_length=3, blank=True, null=True, choices=CHILD_DROPOFF)
    pickup = models.CharField(max_length=3, blank=True, null=True, choices=CHILD_DROPOFF)
    
    class Meta:
        verbose_name_plural = 'Children'
        
    def __unicode__(self):
        return u'%s' % (self.id)
    
class ChildForm(ModelForm):
    grade = ChoiceField(label='What grade is your child in?',
                      choices=CHILD_GRADES,
                      required=False,
                      initial='',)
    to_school = ChoiceField(label='Travel to school (most days)',
                      choices=CHILD_MODES,
                      required=False,)
    from_school = ChoiceField(label='Travel home from school (most days)',
                      choices=CHILD_MODES,
                      required=False,)
    dropoff = ChoiceField(label='Do you usually drop off your child on your way to work or another destination?',
                      choices=CHILD_DROPOFF,
                      required=False,
                      initial='',)
    pickup = ChoiceField(label='Do you usually pick up your child on your way from work or another origin?',
                      choices=CHILD_DROPOFF,
                      required=False,
                      initial='',)
    
    class Meta:
        model = Child
