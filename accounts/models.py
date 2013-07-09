from django.contrib.gis.db import models
from django.contrib.auth.models import User

from survey.models import District, School


class Profile(models.Model):
    user = models.ForeignKey(User, unique=True, verbose_name='user')
    telephone = models.CharField(max_length=20, null=True, blank=False)
    official_title = models.CharField(max_length=50, null=True, blank=False)
    district = models.ForeignKey(District, null=True, blank=False)
    school = models.ForeignKey(School, null=True, blank=True)

    def get_all_fields(self):
        """Returns a list of all field names on the instance."""
        fields = []
        for f in self._meta.fields:

            fname = f.name
            # resolve picklists/choices, with get_xyz_display() function
            get_choice = 'get_'+fname+'_display'
            if hasattr(self, get_choice):
                value = getattr(self, get_choice)()
            else:
                try:
                    value = getattr(self, fname)
                except User.DoesNotExist:
                    value = None

            # only display fields with values and skip some fields entirely
            if f.editable and value and f.name not in ('id','user',):
                fields.append({
                    'label': f.verbose_name,
                    'name': f.name,
                    'value': value,
                })

        return fields

    def __unicode__(self):
        return self.user.username


def user_post_save(sender, instance, **kwargs):
    profile, new = Profile.objects.get_or_create(user=instance)

models.signals.post_save.connect(user_post_save, User)
