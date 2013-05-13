from django.contrib.gis.db import models
from django import forms
from django.contrib.auth.models import User
from fields import CountryField
from django.template.loader import render_to_string

class Profile(models.Model):
    user = models.ForeignKey(User, unique=True, verbose_name='user')
    telephone = models.CharField(max_length=20, null=True, blank=True)
    address1 = models.CharField(max_length=50, null=True, blank=True, verbose_name='Address')
    address2 = models.CharField(max_length=50, null=True, blank=True, verbose_name='')
    city = models.CharField(max_length=50, null=True, blank=True)
    postal = models.CharField(max_length=10, null=True, blank=True, verbose_name='ZIP code')

    def get_all_fields(self):
        """Returns a list of all field names on the instance."""
        fields = []
        for f in self._meta.fields:

            fname = f.name        
            # resolve picklists/choices, with get_xyz_display() function
            get_choice = 'get_'+fname+'_display'
            if hasattr( self, get_choice):
                value = getattr( self, get_choice)()
            else:
                try :
                    value = getattr(self, fname)
                except User.DoesNotExist:
                    value = None

            # only display fields with values and skip some fields entirely
            if f.editable and value and f.name not in ('id', 'status', 'user', 'complete') :

                fields.append(
                  {
                   'label':f.verbose_name, 
                   'name':f.name, 
                   'value':value,
                  }
                )
        return fields
    
    def __unicode__(self):
        return self.user.username
        

def user_post_save(sender, instance, **kwargs):
    profile, new = Profile.objects.get_or_create(user=instance)

models.signals.post_save.connect(user_post_save, User)
