from django.contrib.gis.db import models
from django.db.models import permalink
from django.forms import ModelForm, HiddenInput, TextInput, IntegerField, CharField, ChoiceField
# lazy translation as default on model
from django.utils.translation import ugettext_lazy as _

# workaround for South custom fields issues 
try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ['^django\.contrib\.gis\.db\.models\.fields\.PointField'])
    add_introspection_rules([], ['^django\.contrib\.gis\.db\.models\.fields\.MultiPolygonField'])
    add_introspection_rules([], ['^django\.contrib\.gis\.db\.models\.fields\.MultiLineStringField'])
except ImportError:
    pass

class District(models.Model):
    """ School Districts """
    districtid = models.IntegerField(primary_key=True)
    distname = models.CharField(max_length=35)
    slug = models.SlugField(max_length=35, unique=True)
    startgrade = models.CharField(max_length=2)
    endgrade = models.CharField(max_length=2)
    distcode4 = models.CharField(max_length=4)
    distcode8 = models.CharField(max_length=8)
    
    geometry = models.MultiPolygonField(srid=26986)
    objects = models.GeoManager()
    
    def __unicode__(self):
        return self.distname
    
    class Meta:
        ordering = ['distname']

class School(models.Model):
    """ Schools """
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, blank=True, null=True)
    
    schid = models.CharField('School ID', max_length=8, blank=True, null=True, unique=True)
    address = models.CharField(max_length=150, blank=True, null=True)
    town_mail = models.CharField(max_length=25, blank=True, null=True)
    town = models.CharField(max_length=25, blank=True, null=True)
    state = models.CharField(max_length=2, blank=True, null=True)
    zip = models.CharField(max_length=10, blank=True, null=True)
    principal = models.CharField(max_length=50, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    fax = models.CharField(max_length=15, blank=True, null=True)
    grades = models.CharField(max_length=70, blank=True, null=True)
    schl_type = models.CharField(max_length=3, blank=True, null=True)     
    districtid = models.ForeignKey('District', blank=True, null=True)
    
    survey_incentive = models.TextField(blank=True, null=True)
    survey_active = models.BooleanField('Is Survey School')
    
    # GeoDjango
    geometry = models.PointField(srid=26986)
    objects = models.GeoManager()
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
        
    @permalink
    def get_absolute_url(self):
        return ('survey_school_form', None, { 'school_slug': self.slug, 'district_slug': self.districtid.slug})
        
class Street(models.Model):
    """
    Streets to be returned as type-ahead in street-fields
    to limit the variety of street names and make geocoding
    more accurate.
    """
    name = models.CharField(max_length=240)
    districtid = models.ForeignKey('District', blank=True, null=True)
    
    geometry = models.MultiLineStringField(srid=26986)
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

# Forms

class SurveyForm(ModelForm):
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
        exclude = ('school', 'ip')
        
        widgets = {
            'location': HiddenInput(),         
        }

CHILD_GRADES = (
            ('', '--'),
            ('p', 'Pre-K'),
            ('k', 'K'),
            ('1', '1'),
            ('2', '2'),
            ('3', '3'),
            ('4', '4'),
            ('5', '5'),
            ('6', '6'),
            ('7', '7'),
            ('8', '8'),
            ('9', '9'),
            ('10', '10'),
            ('11', '11'),
            ('12', '12'),
            )

CHILD_MODES = (
            ('', '--'),
            ('w', _('Walk')),
            ('b', _('Bike')),
            ('sb', _('School Bus')),
            ('fv', _('Family Vehicle (only children in your family)')),
            ('cp', _('Carpool (with children from other families)')),
            ('t', _('Transit (city bus, subway, etc.)')),
            ('o', _('Other (skateboard, scooter, inline skates, etc.)'))
            )

CHILD_DROPOFF = (
            ('', '--'),
            ('yes', _('Yes')),
            ('no', _('No')),
            )
    
class Child(models.Model):
    survey = models.ForeignKey('Survey')
    grade = models.CharField(max_length=2, blank=True, null=True, choices=CHILD_GRADES)
    to_school = models.CharField(max_length=2, blank=True, null=True, choices=CHILD_MODES)
    dropoff = models.CharField(max_length=3, blank=True, null=True, choices=CHILD_DROPOFF)
    from_school = models.CharField(max_length=2, blank=True, null=True, choices=CHILD_MODES)    
    pickup = models.CharField(max_length=3, blank=True, null=True, choices=CHILD_DROPOFF)
    
    class Meta:
        verbose_name_plural = 'Children'
        
    def __unicode__(self):
        return u'%s' % (self.id)
    
class ChildForm(ModelForm):
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
