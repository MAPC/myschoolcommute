from django.contrib.gis.db import models
from django.forms import ModelForm, HiddenInput

# Create your models here.
class Letter(models.Model):
    text = models.TextField()

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
    cross_st = models.CharField('Cross Street', max_length=50, blank=True, null=True)
    nr_vehicles = models.IntegerField('Number of vehicles', blank=True, null=True)
    nr_licenses = models.IntegerField('Number of driver licenses', blank=True, null=True)
    # GeoDjango
    location = models.PointField(geography=True) # default SRS 4326
    objects = models.GeoManager()

class SurveyForm(ModelForm):
    class Meta:
        model = Survey
        
        widgets = {
            'location': HiddenInput(),
            'school': HiddenInput(),
        }
    
class Child(models.Model):
    survey = models.ForeignKey('Survey')
    grades = (
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
    grade = models.CharField(max_length=1, blank=True, null=True, choices=grades)
    modes = (
             ('w', 'Walk'),
             ('sb', 'School bus'),
             ('fv', 'Family Vehicle (only children in your family)'),
             ('cp', 'Carpool (children from other families)'),
             ('t', 'Transit (city bus, subway, etc.)'),
             )
    to_school = models.CharField(max_length=2, blank=True, null=True, choices=modes)
    from_school = models.CharField(max_length=2, blank=True, null=True, choices=modes)
    dropoff = (
               ('yes', 'Yes'),
               ('no', 'No'),
               ('n/a', 'N/A'),
               )
    dropoff_to = models.CharField(max_length=3, blank=True, null=True, choices=dropoff)
    dropoff_from = models.CharField(max_length=3, blank=True, null=True, choices=dropoff)
    
    class Meta:
        verbose_name_plural = 'Children'
